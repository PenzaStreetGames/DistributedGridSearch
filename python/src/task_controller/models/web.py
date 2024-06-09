from typing import Optional

import pydantic
import datetime
import uuid

import src.common.models.web as common_web
import src.task_controller.models.core as core


class Subtask(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4
    task_uid: pydantic.UUID4
    subtask_type: core.SubtaskType
    executor_uid: Optional[pydantic.UUID4]
    status: core.SubtaskStatus
    created_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    params: Optional[dict]
    result: Optional[dict]

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=obj.subtask_uid,
            task_uid=obj.task_uid,
            subtask_type=obj.subtask_type,
            executor_uid=obj.executor_uid,
            status=obj.status,
            created_at=obj.created_at,
            finished_at=obj.finished_at,
            params=obj.params,
            result=obj.result,
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=self.subtask_uid,
            task_uid=self.task_uid,
            subtask_type=self.subtask_type,
            executor_uid=self.executor_uid,
            status=self.status,
            created_at=self.created_at,
            finished_at=self.finished_at,
            params=self.params,
            result=self.result,
        )


class Task(pydantic.BaseModel):
    task_uid: pydantic.UUID4
    task_type: core.TaskType
    creator_uid: pydantic.UUID4
    status: core.TaskStatus
    dataset_uid: Optional[pydantic.UUID4]
    created_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    params: Optional[dict]
    result: Optional[dict]
    subtasks: list[Subtask]

    @staticmethod
    def from_core(obj: core.Task) -> 'Task':
        return Task(
            task_uid=obj.task_uid,
            task_type=obj.task_type,
            creator_uid=obj.creator_uid,
            task_status=obj.status,
            created_at=obj.created_at,
            finished_at=obj.finished_at,
            params=obj.params,
            result=obj.result,
            subtasks=[Subtask.from_core(subtask) for subtask in obj.subtasks],
        )

    def to_core(self) -> core.Task:
        return core.Task(
            task_uid=self.task_uid,
            task_type=self.task_type,
            creator_uid=self.creator_uid,
            dataset_uid=self.dataset_uid,
            status=self.status,
            created_at=self.created_at,
            finished_at=self.finished_at,
            params=self.params,
            result=self.result,
            subtasks=[subtask.to_core() for subtask in self.subtasks],
        )


class TaskCreateRequest(pydantic.BaseModel):
    task_type: core.TaskType
    params: dict
    dataset_path: pydantic.DirectoryPath | pydantic.FilePath


class TaskCreateResponse(common_web.BaseResponse):
    task_uid: pydantic.UUID4


class GetTaskRequest(pydantic.BaseModel):
    task_uid: pydantic.UUID4


class GetTaskResponse(common_web.BaseResponse):
    task: Optional[Task]


class GetSubtaskRequest(pydantic.BaseModel):
    subtask_uid: pydantic.UUID4


class GetSubtaskResponse(common_web.BaseResponse):
    subtask: Optional[Subtask]


class GetTasksResponse(common_web.BaseResponse):
    tasks: list[Task]


class GetTaskResultRequest(pydantic.BaseModel):
    task_uid: pydantic.UUID4


class GetTaskResultResponse(common_web.BaseResponse):
    result: Optional[dict]
