import dataclasses
import datetime
import enum
import ipaddress
import uuid


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
