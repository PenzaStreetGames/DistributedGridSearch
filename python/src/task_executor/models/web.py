import enum
from typing import Optional
import uuid

import pydantic

import src.common.models.web as common_web
import src.task_executor.models.core as core

MAGNET_LINK_REGEX = r'urn:btih:([0-9A-Fa-f\d]+)'


class Subtask(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4
    creator_uid: pydantic.UUID4
    dataset_uid: Optional[pydantic.UUID4]
    status: core.SubtaskStatus
    created_at: Optional[pydantic.NaiveDatetime]
    finished_at: Optional[pydantic.NaiveDatetime]

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=obj.subtask_uid,
            creator_uid=obj.creator_uid,
            dataset_uid=obj.dataset_uid,
            status=obj.status,
            created_at=obj.created_at,
            finished_at=obj.finished_at,
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=self.subtask_uid,
            creator_uid=self.creator_uid,
            dataset_uid=self.dataset_uid,
            status=self.status,
            created_at=self.created_at,
            finished_at=self.finished_at,
        )


class SubtaskOfferRequest(pydantic.BaseModel):
    creator_uid: pydantic.UUID4
    subtask_uid: pydantic.UUID4


class SubtaskOfferVerdict(enum.Enum):
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class SubtaskOfferResponse(common_web.BaseResponse):
    verdict: SubtaskOfferVerdict


class SubtaskCreateRequest(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4
    image_tag: str
    dataset_uid: pydantic.UUID4
    magnet_link: str = pydantic.Field(pattern=MAGNET_LINK_REGEX)
    params: dict


class SubtaskCreateResponse(common_web.BaseResponse):
    subtask: Optional[Subtask]


class GetSubtaskRequest(pydantic.BaseModel):
    subtask_uid: uuid.UUID


class GetSubtaskResponse(common_web.BaseResponse):
    subtask: Optional[Subtask]


class GetSubtasksResponse(common_web.BaseResponse):
    subtasks: list[Subtask]


class GetSubtaskResultRequest(pydantic.BaseModel):
    subtask_uid: uuid.UUID


class GetSubtaskResultResponse(common_web.BaseResponse):
    result: Optional[dict]
