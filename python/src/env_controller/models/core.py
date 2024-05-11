import dataclasses
import enum
from typing import Optional
import uuid


class ImageStatus(enum.Enum):
    CREATING = 'creating'
    BUILDING = 'building'
    BUILDING_ERROR = 'building_error'
    PUSHING = 'pushing'
    PUSHING_ERROR = 'pushing_error'
    PUSHED = 'pushed'
    PULLING = 'pulling'
    PULLING_ERROR = 'pulling_error'
    PULLED = 'pulled'
    ARCHIVED = 'archived'


@dataclasses.dataclass
class Image:
    image_tag: str
    image_id: Optional[str]
    status: ImageStatus


class SubtaskStatus(enum.Enum):
    CREATING = 'creating'
    FILE_COPYING = 'file_copying'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'


@dataclasses.dataclass
class Subtask:
    subtask_uid: uuid.UUID
    image: Image
    container_id: Optional[str]
    status: SubtaskStatus


class TaskType(enum.Enum):
    GRID_SEARCH = 'GRID_SEARCH'


class SubtaskType(enum.Enum):
    GRID_SEARCH = 'GRID_SEARCH'
