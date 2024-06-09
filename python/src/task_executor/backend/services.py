import asyncio
import datetime
import ipaddress
import json
import pathlib
import threading
import time
from typing import Iterable, Optional
import uuid

import src.data_controller.client.client as data_client
import src.data_controller.models.core as data_models
import src.env_controller.client.client as env_client
import src.env_controller.models.core as env_models
import src.node_controller.backend.network_service as network
import src.node_controller.backend.services as node_services
import src.task_executor.backend.repositories as repositories
import src.task_executor.models.core as models

ENV_CONTROLLER_HOST = '127.0.0.1'
ENV_CONTROLLER_PORT = 8001
DATA_CONTROLLER_HOST = '127.0.0.1'
DATA_CONTROLLER_PORT = 8002
IMAGE_PULLING_POLLING_DELAY = 0.05
DATASET_DOWNLOADING_POLLING_DELAY = 0.1
CONTAINER_RUNNING_POLLING_DELAY = 0.05


class SubtaskService:
    def __init__(
        self,
        subtask_repository: repositories.SubtaskRepository,
    ):
        self.subtask_repository = subtask_repository
        self.env_controller_client = env_client.EnvControllerClient()
        self.env_controller_client.set_server(
            ipv4_address=ipaddress.IPv4Address(ENV_CONTROLLER_HOST),
            port=ENV_CONTROLLER_PORT,
        )
        self.data_controller_client = data_client.DataControllerClient()
        self.data_controller_client.set_server(
            ipv4_address=ipaddress.IPv4Address(DATA_CONTROLLER_HOST),
            port=DATA_CONTROLLER_PORT,
        )

    def consider_subtask_offer(
        self,
        creator_uid: uuid.UUID,
        subtask_uid: uuid.UUID,
    ) -> bool:
        subtask = models.Subtask(
            subtask_uid=subtask_uid,
            creator_uid=creator_uid,
            dataset_uid=None,
            status=models.SubtaskStatus.WAITING_PARAMS,
            created_at=None,
            finished_at=None,
        )
        self.subtask_repository.create_entity(subtask)
        return True

    async def start_subtask(
        self,
        subtask_uid: uuid.UUID,
        image_tag: str,
        dataset_uid: uuid.UUID,
        magent_link: str,
        params: dict,
    ) -> models.Subtask:
        subtask = self.subtask_repository.get_entity(subtask_uid=subtask_uid)
        await self.data_controller_client.download_dataset(
            dataset_uid=dataset_uid, magnet_link=magent_link,
        )
        await self.env_controller_client.pull_image(image_tag=image_tag)
        subtask.status = models.SubtaskStatus.CREATING
        self.subtask_repository.update_entity(subtask)
        asyncio.create_task(
            self._start_subtask(
                subtask_uid=subtask_uid,
                image_tag=image_tag,
                dataset_uid=dataset_uid,
                params=params,
            ),
        )
        return subtask

    async def _start_subtask(
        self,
        subtask_uid: uuid.UUID,
        image_tag: str,
        dataset_uid: uuid.UUID,
        params: dict,
    ):
        subtask = self.subtask_repository.get_entity(subtask_uid=subtask_uid)
        print(f'waiting pulling image {image_tag}...')
        await self._wait_image_pulling(image_tag=image_tag)
        print(f'image {image_tag} has been pulled')
        print(f'waiting downloading dataset {dataset_uid}...')
        await self._wait_dataset_downloading(dataset_uid=dataset_uid)
        print(f'dataset {dataset_uid} has been downloaded')
        dataset = await self.data_controller_client.get_dataset(dataset_uid)
        dataset_paths = [
            file for file in dataset.path.rglob('*') if file.is_file()
        ]
        config_path = (
            self.subtasks_configs_folder / str(subtask_uid) / 'config.json'
        )
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(params))
        print(f'start running container of subtask {subtask_uid}...')
        await self.env_controller_client.run_container(
            subtask_uid=subtask_uid,
            image_tag=image_tag,
            input_files=[*dataset_paths, config_path],
        )
        print(f'container of subtask {subtask_uid} has been started')
        subtask.status = models.SubtaskStatus.RUNNING
        subtask.created_at = datetime.datetime.now()
        self.subtask_repository.update_entity(subtask)
        print(f'waiting container running of subtask {subtask_uid}...')
        await self._wait_container_running(subtask_uid=subtask_uid)
        print(f'container of subtask {subtask_uid} has been finished')
        subtask.status = models.SubtaskStatus.SUCCESS
        subtask.finished_at = datetime.datetime.now()
        self.subtask_repository.update_entity(subtask)

    def get_subtask(
        self, subtask_uid: uuid.UUID
    ) -> Optional[models.Subtask]:
        subtask = self.subtask_repository.get_entity(subtask_uid)
        return subtask

    def get_subtasks(self) -> Iterable[models.Subtask]:
        subtasks = self.subtask_repository.get_entities()
        return subtasks

    async def get_subtask_result(
        self, subtask_uid: uuid.UUID,
    ) -> Optional[dict]:
        result_path = await self.env_controller_client.get_container_result(
            subtask_uid=subtask_uid,
        )
        if result_path is None:
            return None
        result = json.loads(result_path.read_text())
        return result

    async def _wait_image_pulling(
        self, image_tag: str,
    ):
        status = await self.env_controller_client.get_pull_image_status(
            image_tag=image_tag,
        )
        while status != env_models.ImageStatus.PULLED:
            await asyncio.sleep(IMAGE_PULLING_POLLING_DELAY)
            status = await self.env_controller_client.get_pull_image_status(
                image_tag=image_tag,
            )

    async def _wait_dataset_downloading(
        self, dataset_uid: uuid.UUID,
    ):
        status = await self.data_controller_client.get_dataset(
            dataset_uid=dataset_uid,
        )
        while status.status != data_models.DatasetStatus.AVAILABLE:
            await asyncio.sleep(DATASET_DOWNLOADING_POLLING_DELAY)
            status = await self.data_controller_client.get_dataset(
                dataset_uid=dataset_uid,
            )

    async def _wait_container_running(
        self, subtask_uid: uuid.UUID,
    ):
        status = await self.env_controller_client.get_container_status(
            subtask_uid=subtask_uid
        )
        while status == env_models.SubtaskStatus.RUNNING:
            await asyncio.sleep(CONTAINER_RUNNING_POLLING_DELAY)
            status = await self.env_controller_client.get_container_status(
                subtask_uid=subtask_uid
            )

    @property
    def config_path(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'config' / 'config.json'

    @property
    def subtasks_configs_folder(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'subtasks'
