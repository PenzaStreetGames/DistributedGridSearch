import asyncio
import copy
import datetime
import ipaddress
import math
import pathlib
from typing import Any, Iterable
from typing import Optional
import uuid

import src.data_controller.client.client as data_client
import src.data_controller.models.core as data_models
import src.env_controller.client.client as env_client
import src.env_controller.models.core as env_models
import src.node_controller.backend.network_service as network
import src.node_controller.backend.repositories as node_repositories
import src.node_controller.backend.services as node_services
import src.node_controller.client.client as node_client
import src.node_controller.models.core as node_models
import src.task_controller.backend.repositories as repositories
import src.task_controller.models.core as models
import src.task_executor.client.client as executor_client
import src.task_executor.models.core as executor_models

EXECUTORS_ABSENCE_DELAY = 30.0
IMAGE_PUSHING_POLLING_DELAY = 0.05
DATASET_PUBLISHING_POLLING_DELAY = 0.1
SUBTASKS_RUNNING_POLLING_DELAY = 0.05


class SubtaskService:
    def __init__(self, subtask_repository: repositories.SubtaskRepository):
        self.subtask_repository = subtask_repository

    async def get_subtask(
        self, subtask_uid: uuid.UUID,
    ) -> Optional[models.Subtask]:
        subtask = self.subtask_repository.get_entity(subtask_uid=subtask_uid)
        return subtask


class TaskService:
    def __init__(
        self,
        task_repository: repositories.TaskRepository,
        subtask_service: SubtaskService,
        subtask_repository: repositories.SubtaskRepository,
        node_service: node_services.NodeService,
        node_repository: node_repositories.NodeRepository,
        network_service: network.NetworkService,
    ):
        self.task_repository = task_repository
        self.subtask_service = subtask_service
        self.subtask_repository = subtask_repository
        self.task_executor_client = executor_client.TaskExecutorClient()
        self.env_controller_client = env_client.EnvControllerClient()
        self.data_controller_client = data_client.DataControllerClient()
        self.network_service = network_service
        self.node_service = node_service
        self.node_repository = node_repository

    async def create_task(
        self,
        task_type: models.TaskType,
        dataset_path: pathlib.Path,
        params: dict,
    ) -> models.Task:
        self_node = self.node_service.get_self_node(self.config_path)
        task = models.Task(
            task_uid=uuid.uuid4(),
            task_type=task_type,
            creator_uid=self_node.node_uid,
            status=models.TaskStatus.CREATING,
            dataset_uid=None,
            created_at=datetime.datetime.now(),
            finished_at=None,
            params=params,
            result=None,
            subtasks=[],
        )
        self.task_repository.create_entity(task)
        asyncio.create_task(
            self._create_task(
                task_uid=task.task_uid,
                task_type=task_type,
                dataset_path=dataset_path,
                params=params,
            ),
        )
        return task

    async def _create_task(
        self,
        task_uid: uuid.UUID,
        task_type: models.TaskType,
        dataset_path: pathlib.Path,
        params: dict,
    ):
        task = self.task_repository.get_entity(task_uid=task_uid)
        executors: list[node_models.Node] = []
        while not executors:
            await self._update_nodes_statuses()
            executors = await self._get_active_executors()
            executors, subtasks_uids = await self._offer_subtasks(executors)
            if not executors:
                await asyncio.sleep(EXECUTORS_ABSENCE_DELAY)
        subtasks_params = self._separate_subtasks_params(
            params, len(executors),
        )
        subtask_type = self.get_subtasks_type(task_type=task_type)
        subtasks = self._create_subtasks(
            task_uid=task.task_uid,
            subtasks_uids=subtasks_uids,
            task_type=task_type,
            executors=executors,
            subtasks_params=subtasks_params,
        )
        for subtask in subtasks:
            self.subtask_repository.create_entity(subtask)
        env_task_type = [
            status
            for status in env_models.TaskType
            if status.name == task_type.name
        ][0]
        env_subtask_type = [
            status
            for status in env_models.SubtaskType
            if status.name == subtask_type.name
        ][0]
        image_tag, dataset_uid, magnet_link = await self._publishing_resources(
            task_uid=task.task_uid,
            task_type=env_task_type,
            subtask_type=env_subtask_type,
            dataset_path=dataset_path,
        )
        task.status = models.TaskStatus.SUBTASKS_SENDING
        self.task_repository.update_entity(task)
        await self._send_subtasks(
            executors=executors,
            subtasks=subtasks,
            image_tag=image_tag,
            dataset_uid=dataset_uid,
            magnet_link=magnet_link,
        )
        await self._wait_subtask_execution(
            executors=executors, subtasks=subtasks,
        )
        subtasks_results = await self._get_subtasks_results(
            executors=executors, subtasks=subtasks,
        )
        merged_result = self._merge_results(results=subtasks_results)
        task.status = models.TaskStatus.RESULT_PROCESSING
        self.task_repository.update_entity(task)
        task_result = self._process_task_result(
            merged_result=merged_result, task_type=task_type,
        )
        task.status = models.TaskStatus.SUCCESS
        task.finished_at = datetime.datetime.now()
        task.result = task_result
        self.task_repository.update_entity(task)

    @staticmethod
    def _separate_subtasks_params(
        params: dict, executors_number: int,
    ) -> list[dict]:
        common_params = {
            k: v for k, v in params.items() if k != 'subtasks_params'
        }
        atomic_subtasks: list[dict] = params['subtasks_params']
        subtasks_params: list[list[dict]] = [
            [] for _ in range(executors_number)
        ]
        for i, atomic_task in enumerate(atomic_subtasks):
            bucket = math.floor((i / len(atomic_subtasks)) * executors_number)
            subtasks_params[bucket].append(atomic_task)
        subtasks: list[dict] = [
            copy.deepcopy(common_params) for _ in range(executors_number)
        ]
        for i, subtask_params in enumerate(subtasks_params):
            subtasks[i]['subtask_params'] = subtask_params
        return subtasks

    def _create_subtasks(
        self,
        task_uid: uuid.UUID,
        subtasks_uids: list[uuid.UUID],
        task_type: models.TaskType,
        executors: list[node_models.Node],
        subtasks_params: list[dict]
    ) -> list[models.Subtask]:
        subtasks: list[models.Subtask] = []
        subtask_type = self.get_subtasks_type(task_type=task_type)
        for i in range(len(subtasks_params)):
            subtask_params = subtasks_params[i]
            executor = executors[i]
            subtask = models.Subtask(
                subtask_uid=subtasks_uids[i],
                subtask_type=subtask_type,
                task_uid=task_uid,
                executor_uid=executor.node_uid,
                status=models.SubtaskStatus.WAITING_EXECUTOR_ASSIGNMENT,
                created_at=None,
                finished_at=None,
                params=subtask_params,
                result=None,
            )
            subtasks.append(subtask)
        return subtasks

    @staticmethod
    def get_subtasks_type(task_type: models.TaskType) -> models.SubtaskType:
        mapping = {
            models.TaskType.GRID_SEARCH: models.SubtaskType.GRID_SEARCH,
        }
        return mapping[task_type]

    async def _update_nodes_statuses(self):
        print('refreshing nodes statuses...')
        registries = [
            node
            for node in self.node_service.get_nodes()
            if node.role == node_models.NodeRole.REGISTRY
        ]
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    node_client.NodeControllerClient().set_server(
                        ipv4_address=registry.ipv4_address, port=registry.port,
                    ).exchange_nodes(nodes=[])
                )
                for registry in registries
            ]
        nodes_lists = [task.result() for task in tasks]
        for nodes_list in nodes_lists:
            for node in nodes_list:
                self.node_repository.upsert_entity(node)
        print(
            'nodes statuses has been refreshed '
            f'from {len(registries)} registries'
        )

    async def _get_active_executors(self) -> list[node_models.Node]:
        nodes = self.node_repository.get_entities()
        active_executors = [
            node
            for node in nodes
            if (
                node.status == node_models.NodeStatus.ACTIVE and
                node.role == node_models.NodeRole.EXECUTOR
            )
        ]
        print(f'{len(active_executors)} active executors has been found')
        return active_executors

    async def _offer_subtasks(
        self, executors: list[node_models.Node]
    ) -> tuple[list[node_models.Node], list[uuid.UUID]]:
        self_node = self.node_service.get_self_node(self.config_path)
        subtask_uids: list[uuid.UUID] = []
        print(f'offering subtasks to {len(executors)} active executors')
        async with asyncio.TaskGroup() as tg:
            subtask_uid = uuid.uuid4()
            subtask_uids.append(subtask_uid)
            tasks = [
                tg.create_task(
                    executor_client.TaskExecutorClient().set_server(
                        ipv4_address=executor.ipv4_address, port=executor.port,
                    ).offer_subtask(
                        subtask_uid=subtask_uid,
                        creator_uid=self_node.node_uid,
                    )
                )
                for executor in executors
            ]
        executors_answers = [task.result() for task in tasks]
        agreed_executors: list[node_models.Node] = []
        agreed_executors_tasks_uids: list[uuid.UUID] = []
        for i in range(len(executors)):
            if executors_answers[i]:
                agreed_executors.append(executors[i])
                agreed_executors_tasks_uids.append(subtask_uids[i])
        print(f'got {len(agreed_executors)} agreed executors')
        return agreed_executors, agreed_executors_tasks_uids

    async def _publishing_resources(
        self,
        task_uid: uuid.UUID,
        task_type: models.TaskType,
        subtask_type: models.SubtaskType,
        dataset_path: pathlib.Path,
    ) -> tuple[str, uuid.UUID, str]:
        print(f'publishing task {task_uid} resources')
        task = self.task_repository.get_entity(task_uid=task_uid)
        image_tag, _ = await self.env_controller_client.set_server(
            ipv4_address=ipaddress.IPv4Address('127.0.0.1'), port=8001,
        ).push_image(task_type=task_type, subtask_type=subtask_type)
        dataset_uid = (
            await self.data_controller_client.set_server(
                ipv4_address=ipaddress.IPv4Address('127.0.0.1'), port=8002,
            ).publish_dataset(dataset_path=dataset_path)
        )
        task.status = models.TaskStatus.RESOURCES_PUBLISHING
        task.dataset_uid = dataset_uid
        task.created_at = datetime.datetime.now()
        self.task_repository.update_entity(task)
        print(f'waiting image {image_tag} pushing')
        await self._wait_image_pushing(image_tag=image_tag)
        print(f'image {image_tag} has been pushed')
        print('waiting dataset publishing')
        await self._wait_dataset_publishing(dataset_uid=dataset_uid)
        dataset = await self.data_controller_client.set_server(
            ipv4_address=ipaddress.IPv4Address('127.0.0.1'), port=8002,
        ).get_dataset(dataset_uid=dataset_uid)
        print(f'dataset {dataset_uid} has been published')
        print(f'task {task_uid} resources has been published')
        return image_tag, dataset_uid, dataset.magnet_link

    async def _wait_image_pushing(
        self, image_tag: str,
    ):
        status = await self.env_controller_client.get_pull_image_status(
            image_tag=image_tag,
        )
        while status != env_models.ImageStatus.PUSHED:
            await asyncio.sleep(IMAGE_PUSHING_POLLING_DELAY)
            status = await self.env_controller_client.get_pull_image_status(
                image_tag=image_tag,
            )

    async def _wait_dataset_publishing(
        self, dataset_uid: uuid.UUID,
    ):
        status = await self.data_controller_client.get_dataset(
            dataset_uid=dataset_uid,
        )
        while status.status != data_models.DatasetStatus.AVAILABLE:
            await asyncio.sleep(DATASET_PUBLISHING_POLLING_DELAY)
            status = await self.data_controller_client.get_dataset(
                dataset_uid=dataset_uid,
            )

    async def _send_subtasks(
        self,
        executors: list[node_models.Node],
        subtasks: list[models.Subtask],
        image_tag: str,
        magnet_link: str,
        dataset_uid: uuid.UUID,
    ):
        print('sending subtasks to executors')
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    executor_client.TaskExecutorClient().set_server(
                        ipv4_address=executors[i].ipv4_address,
                        port=executors[i].port,
                    ).start_subtask(
                        subtask_uid=subtasks[i].subtask_uid,
                        image_tag=image_tag,
                        magnet_link=magnet_link,
                        dataset_uid=dataset_uid,
                        params=subtasks[i].params,
                    )
                )
                for i in range(len(executors))
            ]
        executors_subtasks = [task.result() for task in tasks]
        for i in range(len(executors_subtasks)):
            creator_subtask = subtasks[i]
            creator_subtask.status = models.SubtaskStatus.RUNNING
            self.subtask_repository.update_entity(creator_subtask)
        print('subtasks has been sent to executors')

    async def _wait_subtask_execution(
        self,
        executors: list[node_models.Node],
        subtasks: list[models.Subtask]
    ):
        subtasks_done: list[bool] = [False for _ in range(len(subtasks))]
        print('polling subtask running')
        while not all(subtasks_done):
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(
                        executor_client.TaskExecutorClient().set_server(
                            ipv4_address=executors[i].ipv4_address,
                            port=executors[i].port
                        ).get_subtask(subtask_uid=subtasks[i].subtask_uid)
                    )
                    for i in range(len(subtasks))
                ]
            executors_subtasks = [task.result() for task in tasks]
            ended_statuses = {
                executor_models.SubtaskStatus.SUCCESS,
                executor_models.SubtaskStatus.CANCELLED,
                executor_models.SubtaskStatus.ERROR,
                executor_models.SubtaskStatus.TIMEOUT,
            }
            subtasks_done = [
                executor_subtask.status in ended_statuses
                for executor_subtask in executors_subtasks
            ]
            await asyncio.sleep(SUBTASKS_RUNNING_POLLING_DELAY)
        print('subtasks has been finished')

    async def _get_subtasks_results(
        self,
        executors: list[node_models.Node],
        subtasks: list[models.Subtask]
    ) -> list[dict]:
        print('getting subtasks result')
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    executor_client.TaskExecutorClient().set_server(
                        ipv4_address=executors[i].ipv4_address,
                        port=executors[i].port,
                    ).get_subtask_result(subtask_uid=subtasks[i].subtask_uid)
                )
                for i in range(len(subtasks))
            ]
        results = [task.result() for task in tasks]
        print('subtasks result has been got')
        return results

    @staticmethod
    def _merge_results(results: list[Optional[dict]],) -> list[dict]:
        united_result = []
        for result in results:
            united_result.extend(result['result'])
        return united_result

    @staticmethod
    def _process_task_result(
        merged_result: list[dict], task_type: models.TaskType,
    ) -> Optional[dict]:
        if task_type == models.TaskType.GRID_SEARCH:
            answer = max(merged_result, key=lambda x: x['f1_score'])
            return {'result': answer}

    async def get_task(self, task_uid: uuid.UUID) -> Optional[models.Task]:
        task = self.task_repository.get_entity(task_uid=task_uid)
        return task

    async def get_tasks(self) -> Iterable[models.Task]:
        return self.task_repository.get_entities()

    async def get_task_result(self, task_uid: uuid.UUID) -> Optional[dict]:
        task = self.task_repository.get_entity(task_uid=task_uid)
        return task.result

    @property
    def config_path(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'config' / 'config.json'
