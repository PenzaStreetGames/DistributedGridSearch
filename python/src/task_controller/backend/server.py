import contextlib
import pathlib

import fastapi

import src.common.backend.db as database
import src.common.models.web as web_common
import src.node_controller.backend.network_service as network
import src.node_controller.backend.services as node_services
import src.node_controller.backend.repositories as node_repositories
import src.node_controller.models.core as node_core_models
import src.node_controller.models.db as node_db_models
import src.task_controller.backend.repositories as repositories
import src.task_controller.backend.services as services
import src.task_controller.models.db as db_models
import src.task_controller.models.web as models

TASK_CONTROLLER_DEFAULT_PORT = 8004


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    node_service.init_node(
        tasks_service.config_path, node_core_models.NodeRole.CREATOR,
    )
    node_uid = node_service.get_self_node_uid(tasks_service.config_path)
    network_service.init_public_ip_and_port(
        tasks_service.config_path,
        local_port=TASK_CONTROLLER_DEFAULT_PORT,
        description=f'executor node {node_uid}'
    )
    public_ip, public_port = (
        network_service.get_public_ip_and_port_from_config(
            tasks_service.config_path,
        )
    )
    await node_service.notify_node_enabled(tasks_service.config_path)
    yield
    network_service.remove_rule(
        local_port=TASK_CONTROLLER_DEFAULT_PORT, public_port=public_port,
    )


app = fastapi.FastAPI(lifespan=lifespan)
db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'task_controller.sqlite',
)
node_db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'node_controller.sqlite',
)
db = database.DB(db_name=db_name, base=db_models.Base)
node_db = database.DB(db_name=node_db_name, base=node_db_models.Base)
subtask_repository = repositories.SubtaskRepository(db=db)
task_repository = repositories.TaskRepository(db=db)
node_repository = node_repositories.NodeRepository(db=node_db)
network_service = network.NetworkService()
node_service = node_services.NodeService(node_repository, network_service)
subtasks_service = services.SubtaskService(subtask_repository)
tasks_service = services.TaskService(
    task_repository=task_repository,
    subtask_service=subtasks_service,
    subtask_repository=subtask_repository,
    node_service=node_service,
    node_repository=node_repository,
    network_service=network_service,
)


@app.get('/ping')
async def ping():
    return {'status': 'success'}


@app.post('/task/create')
async def create_task(
    request: models.TaskCreateRequest
) -> models.TaskCreateResponse:
    task = await tasks_service.create_task(
        task_type=request.task_type,
        params=request.params,
        dataset_path=request.dataset_path,
    )
    return models.TaskCreateResponse(
        status=web_common.ResponseStatus.SUCCESS,
        task_uid=task.task_uid,
    )


@app.post('/tasks')
async def get_tasks_list() -> models.GetTasksResponse:
    tasks = await tasks_service.get_tasks()
    return models.GetTasksResponse(
        status=web_common.ResponseStatus.SUCCESS, tasks=tasks,
    )


@app.post('/task')
async def get_task(request: models.GetTaskRequest) -> models.GetTaskResponse:
    task = await tasks_service.get_task(task_uid=request.task_uid)
    return models.GetTaskResponse(
        status=web_common.ResponseStatus.SUCCESS, task=task,
    )


@app.post('/task/subtask')
async def get_subtask(
    request: models.GetSubtaskRequest
) -> models.GetSubtaskResponse:
    subtask = await subtasks_service.get_subtask(
        subtask_uid=request.subtask_uid,
    )
    return models.GetSubtaskResponse(
        status=web_common.ResponseStatus.SUCCESS, subtask=subtask,
    )


@app.post('/task/result')
async def get_task_result(
    request: models.GetTaskResultRequest,
) -> models.GetTaskResultResponse:
    task = await tasks_service.get_task(task_uid=request.task_uid)
    return models.GetTaskResultResponse(
        status=web_common.ResponseStatus.SUCCESS, result=task.result,
    )


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=TASK_CONTROLLER_DEFAULT_PORT)
