import dataclasses
import datetime
import enum
import ipaddress
from typing import Optional
import uuid


class SubtaskStatus(enum.Enum):
    WAITING_PARAMS = 'waiting_params'
    CREATING = 'creating'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'


@dataclasses.dataclass
class Subtask:
    subtask_uid: uuid.UUID
    creator_uid: uuid.UUID
    dataset_uid: Optional[uuid.UUID]
    status: SubtaskStatus
    created_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]


class NodeStatus(enum.Enum):
    UNKNOWN = 'unknown'
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class NodeRole(enum.Enum):
    EXECUTOR = 'executor'
    CREATOR = 'creator'
    REGISTRY = 'registry'


@dataclasses.dataclass
class Node:
    node_uid: uuid.UUID
    ipv4_address: ipaddress.IPv4Address
    port: int
    role: NodeRole
    status: NodeStatus
    last_ping: datetime.datetime


class TaskType(enum.Enum):
    GRID_SEARCH = 'GRID_SEARCH'


class SubtaskType(enum.Enum):
    GRID_SEARCH = 'GRID_SEARCH'
