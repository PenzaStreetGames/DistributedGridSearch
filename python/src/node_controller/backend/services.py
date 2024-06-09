import asyncio
import json
import logging
import pathlib

import aiohttp
import datetime
import ipaddress
from typing import Iterable
import uuid

import src.node_controller.models.core as models
import src.node_controller.backend.repositories as repositories
import src.node_controller.backend.network_service as network
import src.node_controller.client.client as node_client

logger = logging.getLogger()
logger.level = logging.DEBUG


class NodeService:
    def __init__(
        self,
        repository: repositories.NodeRepository,
        network_service: network.NetworkService,
    ) -> None:
        self.repository = repository
        self.node_client = node_client.NodeControllerClient()
        self.network_service = network_service

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

    def handle_handshake(
        self,
        node_uid: uuid.UUID,
        ip: ipaddress.IPv4Address,
        port: int,
        role: models.NodeRole,
    ) -> models.Node:
        other_node = models.Node(
            node_uid=node_uid,
            ipv4_address=ip,
            port=port,
            role=role,
            status=models.NodeStatus.ACTIVE,
            last_ping=datetime.datetime.now(),
        )
        self.repository.upsert_entity(other_node)
        public_ip, public_port = (
            self.network_service.get_public_ip_and_port_from_config(
                self.config_path,
            )
        )
        self_node_uid = self.get_self_node_uid(self.config_path)
        self_node_role = self.get_self_node_role()
        return models.Node(
            node_uid=self_node_uid,
            ipv4_address=public_ip,
            port=public_port,
            role=self_node_role,
            status=models.NodeStatus.ACTIVE,
            last_ping=datetime.datetime.now(),
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

    def get_self_node(self, config_path: pathlib.Path) -> models.Node:
        node_uid = self.get_self_node_uid(config_path)
        node_ip, node_port = (
            self.network_service.get_public_ip_and_port_from_config(
                config_path,
            )
        )
        node_role = self.get_self_node_role(config_path)
        return models.Node(
            node_uid=node_uid,
            ipv4_address=node_ip,
            port=node_port,
            role=node_role,
            status=models.NodeStatus.ACTIVE,
            last_ping=datetime.datetime.now(),
        )

    @staticmethod
    def get_self_node_uid(config_path: pathlib.Path) -> uuid.UUID:
        config: dict = json.loads(config_path.read_text())
        return uuid.UUID(config['node_uid'])

    def get_self_node_role(self, config_path: pathlib.Path) -> models.NodeRole:
        config: dict = json.loads(config_path.read_text())
        return [
            role for role in models.NodeRole if role.value == config['role']
        ][0]

    def init_node(self, config_path: pathlib.Path, role: models.NodeRole):
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({}))
        config = json.loads(config_path.read_text())
        if 'node_uid' not in config:
            config['node_uid'] = str(uuid.uuid4())
        if 'role' not in config:
            config['role'] = role.value
        config_path.write_text(json.dumps(config, indent=2))

    @property
    def config_path(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'config' / 'config.json'

    def is_standalone(self) -> bool:
        nodes = self.repository.get_entities()
        nodes = [
            node for node in nodes if node.role == models.NodeRole.REGISTRY
        ]
        return not bool(nodes)

    async def discover_registry_nodes(self, config_path: pathlib.Path):
        if not config_path.exists():
            print(
                f'node has not config_file {config_path}, '
                'running in standalone mode'
            )
            return
        config = json.loads(config_path.read_text())
        registries = config.get('registries', [])
        if not registries:
            print(
                'node has not bootstrap registries, '
                'running in standalone mode'
            )
            return
        self_node = self.get_self_node(config_path)
        print('polling bootstrap registries')
        for registry in registries:
            registry_ip = ipaddress.IPv4Address(registry['ip'])
            registry_port = registry['port']
            print(f'handshake with {registry_ip}:{registry_port}')
            registry = await self.node_client.set_server(
                ipv4_address=ipaddress.IPv4Address(registry_ip),
                port=registry_port,
            ).handshake(self_node)
            if registry is not None:
                print(
                    f'handshake with {registry_ip}:{registry_port} successful'
                )
                self.repository.upsert_entity(registry)
            else:
                print(f'handshake timeout {registry_ip}:{registry_port}')
        if self.is_standalone():
            print('no one registry not available, running in standalone mode')
            return
        print('registry nodes has been successfully finished')

    async def notify_node_enabled(self, config_path: pathlib.Path):
        if self.is_standalone():
            await self.discover_registry_nodes(config_path)
        self_node = self.get_self_node(config_path)
        nodes = self.repository.get_entities()
        registries = [
            node for node in nodes if node.role == models.NodeRole.REGISTRY
        ]
        print(
            f'notifying {len(registries)} registries '
            f'about node {self_node.node_uid} enabled',
        )
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    node_client.NodeControllerClient().set_server(
                        ipv4_address=registry.ipv4_address, port=registry.port,
                    ).enable_node(
                        node_uid=self_node.node_uid,
                        ipv4_address=self_node.ipv4_address,
                        port=self_node.port,
                    ),
                )
                for registry in registries
            ]
        results = [task.result() for task in tasks]
        print(f'notification has been received {sum(results)} registries')

