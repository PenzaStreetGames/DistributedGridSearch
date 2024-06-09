import pathlib
import uuid

import aiohttp

import src.common.client.client as client_base
import src.env_controller.models.core as models
import src.env_controller.models.web as web


class EnvControllerClient(client_base.ClientBase):

    async def push_image(
        self, task_type: models.TaskType, subtask_type: models.SubtaskType,
    ) -> tuple[str, models.ImageStatus]:
        url = self.get_server_url('/image/push')
        request_body = web.ImagePushRequest(
            task_type=task_type, subtask_type=subtask_type,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ImagePushResponse.model_validate(json)
        return response_body.image_tag, response_body.pushing_status

    async def get_push_image_status(
        self, image_tag: str,
    ) -> models.ImageStatus:
        url = self.get_server_url('/image/push/status')
        request_body = web.ImagePushStatusRequest(
            image_tag=image_tag,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ImagePushStatusResponse.model_validate(json)
        return response_body.pushing_status

    async def pull_image(self, image_tag: str) -> models.ImageStatus:
        url = self.get_server_url('/image/pull')
        request_body = web.ImagePullRequest(
            image_tag=image_tag,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ImagePullResponse.model_validate(json)
        return response_body.pulling_status

    async def get_pull_image_status(self, image_tag: str) -> models.ImageStatus:
        url = self.get_server_url('/image/pull/status')
        request_body = web.ImagePushStatusRequest(
            image_tag=image_tag,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ImagePullStatusResponse.model_validate(json)
        return response_body.pulling_status

    async def run_container(
        self,
        subtask_uid: uuid.UUID,
        image_tag: str,
        input_files: list[pathlib.Path]
    ) -> models.SubtaskStatus:
        url = self.get_server_url('/container/run')
        request_body = web.ContainerRunRequest(
            subtask_uid=subtask_uid,
            image_tag=image_tag,
            input_files=input_files,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ContainerRunResponse.model_validate(json)
        return response_body.running_status

    async def get_container_status(
        self, subtask_uid: uuid.UUID,
    ) -> models.SubtaskStatus:
        url = self.get_server_url('/container/status')
        request_body = web.ContainerStatusRequest(
            subtask_uid=subtask_uid,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ContainerRunResponse.model_validate(json)
        return response_body.running_status

    async def get_container_result(
        self, subtask_uid: uuid.UUID,
    ) -> pathlib.Path:
        url = self.get_server_url('/container/result')
        request_body = web.ContainerResultRequest(
            subtask_uid=subtask_uid,
        ).model_dump(mode='json')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ContainerResultResponse.model_validate(json)
        return response_body.result_file
