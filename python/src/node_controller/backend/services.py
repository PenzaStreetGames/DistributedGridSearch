import asyncio
import logging

import aiohttp
import datetime
import ipaddress
from typing import Iterable
import uuid

import src.node_controller.models.core as models
import src.node_controller.backend.repositories as repositories
import src.node_controller.client.client as node_client

logger = logging.getLogger()
logger.level = logging.DEBUG


class NodeService:
    def __init__(self, repository: repositories.NodeRepository) -> None:
        self.repository = repository
        self.node_client = node_client.NodeControllerClient()

    def create_node(
        self,
        ipv4_address: ipaddress.IPv4Address,
        port: int,
        role: models.NodeRole,
    ) -> models.Node:
        node = models.Node(
            node_uid=uuid.uuid4(),
            ipv4_address=ipv4_address,
            port=port,
            role=role,
            status=models.NodeStatus.ACTIVE,
            last_ping=datetime.datetime.now(),
        )
        self.repository.create_entity(node)
        return node

    def delete_node(self, node_uid: uuid.UUID):
        self.repository.delete_entity(node_uid)

    def enable_node(
        self,
        node_uid: uuid.UUID,
        ipv4_address: ipaddress.IPv4Address,
        port: int,
    ):
        node = self.repository.get_entity(node_uid)
        node.status = models.NodeStatus.ACTIVE
        node.ipv4_address = ipv4_address
        node.port = port
        self.repository.update_entity(node)

    def disable_node(self, node_uid: uuid.UUID):
        node = self.repository.get_entity(node_uid)
        node.status = models.NodeStatus.INACTIVE
        self.repository.update_entity(node)

    def get_nodes(self) -> Iterable[models.Node]:
        return self.repository.get_entities()

    def get_active_nodes(self) -> Iterable[models.Node]:
        return self.repository.get_entities(status=models.NodeStatus.ACTIVE)

    def get_active_executors(self) -> Iterable[models.Node]:
        return self.repository.get_entities(
            role=models.NodeRole.EXECUTOR, status=models.NodeStatus.ACTIVE,
        )

    def exchange_nodes(
        self, nodes: Iterable[models.Node],
    ) -> Iterable[models.Node]:
        known_nodes = self.repository.get_entities()
        known_nodes_keys = {node.node_uid for node in known_nodes}
        for node in nodes:
            if node.node_uid in known_nodes_keys:
                self.repository.update_entity(node)
            else:
                self.repository.create_entity(node)
        logger.info('exchanging nodes')
        return known_nodes

    async def update_nodes_status(self):
        nodes = self.get_nodes()
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self.node_client.set_server(
                        node.ipv4_address, node.port
                    ).ping_node()
                )
                for node in nodes
            ]
        node_statuses = [task.result() for task in tasks]
        for i, node in enumerate(nodes):
            new_status = node_statuses[i]
            if node.status == new_status:
                continue
            if new_status == models.NodeStatus.INACTIVE:
                logger.info(
                    f'updating node({node.node_uid}) status: inactive',
                )
                self.disable_node(node_uid=node.node_uid)
            elif new_status == models.NodeStatus.ACTIVE:
                logger.info(
                    f'updating node({node.node_uid}) status: active',
                )
                self.enable_node(
                    node_uid=node.node_uid,
                    ipv4_address=node.ipv4_address,
                    port=node.port,
                )


