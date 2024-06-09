from typing import Optional
import uuid

import aiohttp

import src.common.client.client as client_base
import src.task_executor.models.core as models
import src.task_executor.models.web as web


class TaskExecutorClient(client_base.ClientBase):
    async def offer_subtask(
        self, creator_uid: uuid.UUID, subtask_uid: uuid.UUID,
    ) -> bool:
        url = self.get_server_url('/subtask/offer')
        request_body = web.SubtaskOfferRequest(
            creator_uid=creator_uid, subtask_uid=subtask_uid,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.SubtaskOfferResponse.model_validate(json)
        return response_body.verdict == web.SubtaskOfferVerdict.ACCEPTED

    async def start_subtask(
        self,
        subtask_uid: uuid.UUID,
        image_tag: str,
        dataset_uid: uuid.UUID,
        magnet_link: str,
        params: dict,
    ) -> Optional[models.Subtask]:
        url = self.get_server_url('/subtask/start')
        request_body = web.SubtaskCreateRequest(
            subtask_uid=subtask_uid,
            image_tag=image_tag,
            dataset_uid=dataset_uid,
            magnet_link=magnet_link,
            params=params,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.SubtaskCreateResponse.model_validate(json)
        return response_body.subtask

    async def get_subtask(
        self, subtask_uid: uuid.UUID,
    ) -> Optional[models.Subtask]:
        url = self.get_server_url('/subtask')
        request_body = web.GetSubtaskRequest(
            subtask_uid=subtask_uid,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.GetSubtaskResponse.model_validate(json)
        return response_body.subtask

    async def get_subtasks(self) -> list[models.Subtask]:
        url = self.get_server_url('/subtasks')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={}) as response:
                json = await response.json()
        response_body = web.GetSubtasksResponse.model_validate(json)
        return response_body.subtasks

    async def get_subtask_result(
        self, subtask_uid: uuid.UUID,
    ) -> Optional[dict]:
        url = self.get_server_url('/subtask/result')
        request_body = web.GetSubtaskResultRequest(
            subtask_uid=subtask_uid,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.GetSubtaskResultResponse.model_validate(json)
        return response_body.result
