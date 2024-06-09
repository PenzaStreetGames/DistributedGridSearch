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
import src.task_executor.backend.repositories as repositories
import src.task_executor.backend.services as services
import src.task_executor.models.db as db_models
import src.task_executor.models.web as models


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    node_service.init_node(
        subtasks_service.config_path, node_core_models.NodeRole.EXECUTOR,
    )
    node_uid = node_service.get_self_node_uid(subtasks_service.config_path)
    network_service.init_public_ip_and_port(
        subtasks_service.config_path,
        local_port=8003,
        description=f'executor node {node_uid}'
    )
    public_ip, public_port = (
        network_service.get_public_ip_and_port_from_config(
            subtasks_service.config_path,
        )
    )
    await node_service.notify_node_enabled(subtasks_service.config_path)
    yield
    network_service.remove_rule(local_port=8003, public_port=public_port)


app = fastapi.FastAPI(lifespan=lifespan)
db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'task_executor.sqlite',
)
node_db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'node_controller.sqlite',
)
db = database.DB(db_name=db_name, base=db_models.Base)
node_db = database.DB(db_name=node_db_name, base=node_db_models.Base)
subtask_repository = repositories.SubtaskRepository(db=db)
node_repository = node_repositories.NodeRepository(db=node_db)
network_service = network.NetworkService()
node_service = node_services.NodeService(node_repository, network_service)
subtasks_service = services.SubtaskService(subtask_repository)


@app.get('/ping')
async def ping():
    return {'status': 'success'}


@app.post('/subtask/offer')
async def offer_subtask(
    request: models.SubtaskOfferRequest,
) -> models.SubtaskOfferResponse:
    accepted = subtasks_service.consider_subtask_offer(
        creator_uid=request.creator_uid, subtask_uid=request.subtask_uid,
    )
    verdict = (
        models.SubtaskOfferVerdict.ACCEPTED
        if accepted
        else models.SubtaskOfferVerdict.DECLINED
    )
    return models.SubtaskOfferResponse(
        status=web_common.ResponseStatus.SUCCESS, verdict=verdict,
    )


@app.post('/subtask/start')
async def start_subtask(
    request: models.SubtaskCreateRequest,
) -> models.SubtaskCreateResponse:
    subtask = await subtasks_service.start_subtask(
        subtask_uid=request.subtask_uid,
        image_tag=request.image_tag,
        dataset_uid=request.dataset_uid,
        magent_link=request.magnet_link,
        params=request.params,
    )
    return models.SubtaskCreateResponse(
        status=web_common.ResponseStatus.SUCCESS,
        subtask=models.Subtask.from_core(subtask),
    )


@app.post('/subtask')
async def get_subtask(
    request: models.GetSubtaskRequest,
) -> models.GetSubtaskResponse:
    subtask = subtasks_service.get_subtask(request.subtask_uid)
    return models.GetSubtaskResponse(
        status=web_common.ResponseStatus.SUCCESS,
        subtask=(
            models.Subtask.from_core(subtask) if subtask is not None else None
        ),
    )


@app.post('/subtasks')
async def get_subtasks() -> models.GetSubtasksResponse:
    subtasks = subtasks_service.get_subtasks()
    return models.GetSubtasksResponse(
        status=web_common.ResponseStatus.SUCCESS,
        subtasks=[models.Subtask.from_core(subtask) for subtask in subtasks],
    )


@app.post('/subtask/result')
async def get_subtask_result(
    request: models.GetSubtaskResultRequest
) -> models.GetSubtaskResultResponse:
    result = await subtasks_service.get_subtask_result(
        subtask_uid=request.subtask_uid,
    )
    return models.GetSubtaskResultResponse(
        status=web_common.ResponseStatus.SUCCESS,
        result=result,
    )


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8003)
