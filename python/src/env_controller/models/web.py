from typing import Optional

import pydantic

import src.common.models.web as common_web
import src.env_controller.models.core as core


SHA_256_REGEX = r'[A-Fa-f0-9]{64}'


class Image(pydantic.BaseModel):
    image_tag: str = pydantic.Field(max_length=256)
    image_id: Optional[str] = pydantic.Field(pattern=SHA_256_REGEX)
    status: core.ImageStatus

    @staticmethod
    def from_core(obj: core.Image) -> 'Image':
        return Image(
            image_tag=obj.image_tag,
            image_id=obj.image_id,
            status=obj.status,
        )

    def to_core(self) -> core.Image:
        return core.Image(
            image_tag=self.image_tag,
            image_id=self.image_id,
            status=self.status,
        )


class Subtask(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4
    image: Image
    container_id: Optional[str] = pydantic.Field(pattern=SHA_256_REGEX)
    status: core.SubtaskStatus

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=obj.subtask_uid,
            image=Image.from_core(obj.image),
            container_id=obj.container_id,
            status=obj.status,
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=self.subtask_uid,
            image=self.image.to_core(),
            container_id=self.container_id,
            status=self.status,
        )


class ImagePushRequest(pydantic.BaseModel):
    task_type: core.TaskType
    subtask_type: core.SubtaskType


class ImagePushResponse(common_web.BaseResponse):
    image_tag: str
    pushing_status: core.ImageStatus


class ImagePushStatusRequest(pydantic.BaseModel):
    image_tag: str


class ImagePushStatusResponse(common_web.BaseResponse):
    image_tag: str
    pushing_status: core.ImageStatus


class ImagePullRequest(pydantic.BaseModel):
    image_tag: str


class ImagePullResponse(common_web.BaseResponse):
    image_tag: str
    pulling_status: core.ImageStatus


class ImagePullStatusRequest(pydantic.BaseModel):
    image_tag: str


class ImagePullStatusResponse(common_web.BaseResponse):
    image_tag: str
    pulling_status: core.ImageStatus


class ContainerRunRequest(pydantic.BaseModel):
    image_tag: str
    subtask_uid: pydantic.UUID4
    input_files: list[pydantic.FilePath]


class ContainerRunResponse(common_web.BaseResponse):
    subtask_uid: pydantic.UUID4
    running_status: core.SubtaskStatus


class ContainerStatusRequest(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4


class ContainerStatusResponse(common_web.BaseResponse):
    subtask_uid: pydantic.UUID4
    running_status: core.SubtaskStatus


class ContainerResultRequest(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4


class ContainerResultResponse(common_web.BaseResponse):
    subtask_uid: pydantic.UUID4
    result_file: pydantic.FilePath

