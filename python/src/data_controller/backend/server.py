import pathlib

import fastapi

import src.common.backend.db as database
import src.common.models.web as common_web
import src.data_controller.backend.repositories as repositories
import src.data_controller.backend.services as services
import src.data_controller.backend.torrent_service as torrent
import src.data_controller.models.db as db_models
import src.data_controller.models.web as models


app = fastapi.FastAPI()
db_name = str(
    pathlib.Path(__file__).parent.parent / 'db' / 'data_controller.sqlite',
)
print(db_name)
db = database.DB(db_name=db_name, base=db_models.Base)
dataset_repository = repositories.DatasetRepository(db)
torrent_service = torrent.TorrentService(dataset_repository)
dataset_service = services.DatasetService(dataset_repository, torrent_service)


@app.post('/data/publish')
def publish_dataset(
    request: models.DataPublishRequest,
) -> models.DataPublishResponse:
    dataset = dataset_service.publish_dataset(request.path)
    return models.DataPublishResponse(
        status=common_web.ResponseStatus.SUCCESS,
        dataset_uid=dataset.dataset_uid,
    )


@app.post('/data/download')
def download_dataset(
    request: models.DataDownloadRequest,
) -> models.DataDownloadResponse:
    dataset = dataset_service.download_dataset(
        request.dataset_uid, request.magnet_link,
    )
    return models.DataDownloadResponse(
        status=common_web.ResponseStatus.SUCCESS,
        dataset_uid=dataset.dataset_uid,
    )


@app.post('/data')
def get_dataset(request: models.GetDataRequest) -> models.Dataset:
    dataset = dataset_service.get_dataset(request.dataset_uid)
    return models.Dataset.from_core(dataset)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8002)
