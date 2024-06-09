import dataclasses
import datetime
import enum
from typing import Optional
import uuid


class SubtaskType(enum.Enum):
    GRID_SEARCH = 'grid_search'


class SubtaskStatus(enum.Enum):
    WAITING_EXECUTOR_ASSIGNMENT = 'waiting_executor_assignment'
    CREATING = 'creating'
    RESOURCES_DOWNLOADING = 'resources_downloading'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'


@dataclasses.dataclass
class Subtask:
    subtask_uid: uuid.UUID
    task_uid: uuid.UUID
    subtask_type: SubtaskType
    executor_uid: Optional[uuid.UUID]
    status: SubtaskStatus
    created_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    params: Optional[dict]
    result: Optional[dict]


class TaskType(enum.Enum):
    GRID_SEARCH = 'grid_search'


class TaskStatus(enum.Enum):
    CREATING = 'creating'
    EXECUTORS_SEARCHING = 'executors_searching'
    RESOURCES_PUBLISHING = 'resources_publishing'
    SUBTASKS_SENDING = 'subtasks_sending'
    SUBTASKS_POLLING = 'subtasks_polling'
    RESULT_PROCESSING = 'result_processing'
    SUCCESS = 'success'
    ERROR = 'error'


@dataclasses.dataclass
class Task:
    task_uid: uuid.UUID
    task_type: TaskType
    creator_uid: uuid.UUID
    status: TaskStatus
    dataset_uid: Optional[uuid.UUID]
    created_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    params: Optional[dict]
    result: Optional[dict]
    subtasks: list[Subtask]
