import pathlib

import fastapi

import src.common.backend.db as database
import src.common.models.web as common_models
import src.env_controller.backend.docker_service as docker
import src.env_controller.backend.repositories as repositories
import src.env_controller.backend.services as services
import src.env_controller.models.web as models
import src.env_controller.models.db as db_models

app = fastapi.FastAPI()
db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'env_controller.sqlite',
)
db = database.DB(db_name=db_name, base=db_models.Base)
image_repository = repositories.ImageRepository(db=db)
subtask_repository = repositories.SubtaskRepository(db=db)
docker_service = docker.DockerService(image_repository, subtask_repository)
image_service = services.ImageService(image_repository, docker_service)
subtasks_service = services.SubtaskService(
    subtask_repository, image_repository, docker_service,
)


@app.post('/image/push')
async def push_image(
    request: models.ImagePushRequest,
) -> models.ImagePushResponse:
    image = image_service.build_and_push(
        task_type=request.task_type, subtask_type=request.subtask_type,
    )
    return models.ImagePushResponse(
        status=common_models.ResponseStatus.SUCCESS,
        image_tag=image.image_tag,
        pushing_status=image.status,
    )


@app.post('/image/push/status')
async def push_image_status(
    request: models.ImagePushStatusRequest,
) -> models.ImagePushStatusResponse:
    status = image_service.get_image_status(request.image_tag)
    return models.ImagePushStatusResponse(
        status=common_models.ResponseStatus.SUCCESS,
        image_tag=request.image_tag,
        pushing_status=status,
    )


@app.post('/image/pull')
async def pull_image(
    request: models.ImagePullRequest,
) -> models.ImagePullResponse:
    image = image_service.pull_image(image_tag=request.image_tag)
    return models.ImagePullResponse(
        status=common_models.ResponseStatus.SUCCESS,
        image_tag=image.image_tag,
        pulling_status=image.status,
    )


@app.post('/image/pull/status')
async def pull_image_status(
    request: models.ImagePullStatusRequest,
) -> models.ImagePullStatusResponse:
    status = image_service.get_image_status(image_tag=request.image_tag)
    return models.ImagePullStatusResponse(
        status=common_models.ResponseStatus.SUCCESS,
        image_tag=request.image_tag,
        pulling_status=status,
    )


@app.post('/container/run')
async def run_container(
    request: models.ContainerRunRequest,
) -> models.ContainerRunResponse:
    subtask = subtasks_service.run_container(
        subtask_uid=request.subtask_uid,
        image_tag=request.image_tag,
        input_files=request.input_files,
    )
    return models.ContainerRunResponse(
        status=common_models.ResponseStatus.SUCCESS,
        subtask_uid=request.subtask_uid,
        running_status=subtask.status,
    )


@app.post('/container/status')
async def get_container_status(
    request: models.ContainerStatusRequest,
) -> models.ContainerStatusResponse:
    status = subtasks_service.get_container_status(request.subtask_uid)
    return models.ContainerStatusResponse(
        status=common_models.ResponseStatus.SUCCESS,
        subtask_uid=request.subtask_uid,
        running_status=status,
    )


@app.post('/container/result')
async def get_container_result(
    request: models.ContainerResultRequest,
) -> models.ContainerResultResponse:
    result_file = subtasks_service.get_subtask_result(request.subtask_uid)
    return models.ContainerResultResponse(
        status=common_models.ResponseStatus.SUCCESS,
        subtask_uid=request.subtask_uid,
        result_file=result_file,
    )


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8001)
