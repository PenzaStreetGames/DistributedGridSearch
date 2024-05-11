import pathlib
import uuid

import aiohttp

import src.common.client.client as client_base
import src.data_controller.models.core as models
import src.data_controller.models.web as web


class DatasetClient(client_base.ClientBase):
    async def publish_dataset(self, dataset_path: pathlib.Path) -> uuid.UUID:
        url = self.get_server_url('/data/publish')
        request_body = web.DataPublishRequest(
            path=dataset_path,
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.DataPublishResponse.model_validate(json)
        return response_body.dataset_uid

    async def download_dataset(
        self, dataset_uid: uuid.UUID, magnet_link: str,
    ) -> None:
        url = self.get_server_url('/data/download')
        request_body = web.DataDownloadRequest(
            dataset_uid=dataset_uid, magnet_link=magnet_link,
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                await response.json()

    async def get_dataset(self, dataset_uid: uuid.UUID) -> models.Dataset:
        url = self.get_server_url('/data')
        request_body = web.GetDataRequest(
            dataset_uid=dataset_uid,
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.Dataset.model_validate(json)
        return response_body.dataset_uid
