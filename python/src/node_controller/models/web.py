import enum
from typing import Optional
import uuid

import pydantic.networks

import src.common.models.web as common_web
import src.node_controller.models.core as core


class Node(pydantic.BaseModel):
    node_uid: pydantic.UUID4
    ipv4_address: pydantic.networks.IPv4Address
    port: int = pydantic.Field(ge=0, le=65535)
    role: core.NodeRole
    status: core.NodeStatus
    last_ping: pydantic.NaiveDatetime

    @staticmethod
    def from_core(obj: core.Node) -> 'Node':
        return Node(
            node_uid=obj.node_uid,
            ipv4_address=obj.ipv4_address,
            port=obj.port,
            role=obj.role,
            status=obj.status,
            last_ping=obj.last_ping,
        )

    def to_core(self) -> core.Node:
        return core.Node(
            node_uid=self.node_uid,
            ipv4_address=self.ipv4_address,
            port=self.port,
            role=self.role,
            status=self.status,
            last_ping=self.last_ping,
        )


class Nodes(pydantic.BaseModel):
    nodes: list[Node]


class HandshakeRequest(pydantic.BaseModel):
    node_uid: uuid.UUID
    ip: pydantic.networks.IPv4Address
    port: int
    role: core.NodeRole


class HandshakeResponse(common_web.BaseResponse):
    node_uid: uuid.UUID
    ip: pydantic.networks.IPv4Address
    port: int
    role: core.NodeRole


class JoinRequest(pydantic.BaseModel):
    ip: pydantic.networks.IPv4Address
    port: int = pydantic.Field(ge=0, le=65535)
    role: core.NodeRole


class JoinResponse(pydantic.BaseModel):
    node_uid: pydantic.UUID4


class LeaveRequest(pydantic.BaseModel):
    node_uid: pydantic.UUID4


class LeaveResponse(common_web.BaseResponse):
    pass


class EnableRequest(pydantic.BaseModel):
    node_uid: pydantic.UUID4
    ip: pydantic.networks.IPv4Address
    port: int = pydantic.Field(ge=0, le=65535)


class EnableResponse(common_web.BaseResponse):
    pass


class DisableRequest(pydantic.BaseModel):
    node_uid: pydantic.UUID4


class DisableResponse(common_web.BaseResponse):
    pass


class ExchangeRequest(pydantic.BaseModel):
    nodes: list[Node]


class ExchangeResponse(pydantic.BaseModel):
    nodes: list[Node]
