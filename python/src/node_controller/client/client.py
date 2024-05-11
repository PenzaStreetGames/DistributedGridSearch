import asyncio
import ipaddress
from typing import Iterable
import uuid

import aiohttp

import src.common.client.client as client_base
import src.node_controller.models.core as models
import src.node_controller.models.web as web


class NodeControllerClient(client_base.ClientBase):
    async def ping_node(self) -> models.NodeStatus:
        url = self.get_server_url('/nodes/ping')
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=3) as response:
                    await response.json()
                    return models.NodeStatus.ACTIVE
            except asyncio.TimeoutError:
                return models.NodeStatus.INACTIVE

    async def get_active_nodes(self) -> list[models.Node]:
        url = self.get_server_url('/nodes/active')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={}) as response:
                json = await response.json()
        response_body = web.Nodes.model_validate(json)
        return [node.to_core() for node in response_body.nodes]

    async def exchange_nodes(
        self, nodes: Iterable[models.Node],
    ) -> list[models.Node]:
        url = self.get_server_url('/nodes/exchange')
        request_body = web.ExchangeRequest(
            nodes=[web.Node.from_core(node) for node in nodes],
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.ExchangeResponse.model_validate(json)
        return [node.to_core() for node in response_body.nodes]

    async def join_node(
        self,
        ipv4_address: ipaddress.IPv4Address,
        port: int,
        role: models.NodeRole,
    ) -> uuid.UUID:
        url = self.get_server_url('/nodes/join')
        request_body = web.JoinRequest(
            ipv4_address=ipv4_address, port=port, role=role,
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.JoinResponse.model_validate(json)
        return response_body.node_uid

    async def leave_node(
        self,
        node_uid: uuid.UUID,
    ) -> bool:
        url = self.get_server_url('/nodes/leave')
        request_body = web.LeaveRequest(node_uid=node_uid).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.LeaveResponse.model_validate(json)
        return response_body.status == web.ResponseStatus.SUCCESS

    async def enable_node(
        self,
        ipv4_address: ipaddress.IPv4Address,
        port: int,
        node_uid: uuid.UUID,
    ) -> bool:
        url = self.get_server_url('/nodes/enable')
        request_body = web.EnableRequest(
            ipv4_address=ipv4_address, port=port, node_uid=node_uid,
        ).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.EnableResponse.model_validate(json)
        return response_body.status == web.ResponseStatus.SUCCESS

    async def disable_node(self, node_uid: uuid.UUID) -> bool:
        url = self.get_server_url('/nodes/disable')
        request_body = web.DisableRequest(node_uid=node_uid).model_dump()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_body) as response:
                json = await response.json()
        response_body = web.DisableResponse.model_validate(json)
        return response_body.status == web.ResponseStatus.SUCCESS

