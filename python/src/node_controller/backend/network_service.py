import ipaddress
import json
import pathlib
import socket
from typing import Optional

import upnpclient

MIN_PUBLIC_PORT = 50000
MAX_PUBLIC_PORT = 51000


class NetworkService:
    def __init__(self):
        self.device = self._get_device()

    @staticmethod
    def _get_device() -> upnpclient.Device:
        print('discovery public gateway device')
        device = upnpclient.discover()[0]
        print('device has been discovered')
        return device

    def get_public_ip(self) -> ipaddress.IPv4Address:
        service = self.device.WANIPConn1
        return service.GetExternalIPAddress()['NewExternalIPAddress']

    @staticmethod
    def get_local_ip() -> ipaddress.IPv4Address:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ipaddress.IPv4Address(ip)

    def get_upnp_rules(self) -> dict[str, str]:
        rules: list[dict] = []
        i: int = 0
        service = self.device.WANIPConn1
        while True:
            try:
                row = service.GetGenericPortMappingEntry(
                    NewPortMappingIndex=i,
                )
                rules.append(row)
                i += 1
            except upnpclient.soap.SOAPError:
                break
        mapping: dict[str, str] = {}
        for rule in rules:
            public_port = rule['NewExternalPort']
            local_ip = rule['NewInternalClient']
            local_port = rule['NewInternalPort']
            mapping[public_port] = f'{local_ip}:{local_port}'
        return mapping

    def get_free_public_port(self) -> Optional[int]:
        rules = self.get_upnp_rules()
        for port in range(MIN_PUBLIC_PORT, MAX_PUBLIC_PORT):
            if port not in rules:
                return port
        return None

    @staticmethod
    def get_free_local_port() -> int:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def set_rule(
        self,
        local_ip: ipaddress.IPv4Address,
        local_port: int,
        public_port: int,
        description: str = 'dist_calc port mapping',
    ):
        service = self.device.WANIPConn1
        service.AddPortMapping(
            NewRemoteHost='',
            NewExternalPort=public_port,
            NewProtocol='TCP',
            NewInternalPort=local_port,
            NewInternalClient=local_ip,
            NewEnabled='1',
            NewPortMappingDescription=description,
            NewLeaseDuration=86400,
        )
        public_ip = self.get_public_ip()
        print(
            'create mapping '
            f'{local_ip}:{local_port} -> {public_ip}:{public_port}',
        )

    def remove_rule(
        self,
        local_port: int,
        public_port: int,
    ):
        service = self.device.WANIPConn1
        service.DeletePortMapping(
            NewRemoteHost='',
            NewExternalPort=public_port,
            NewProtocol='TCP',
        )
        local_ip = self.get_local_ip()
        public_ip = self.get_public_ip()
        print(
            'remove mapping '
            f'{local_ip}:{local_port} -> {public_ip}:{public_port}',
        )

    def init_public_ip_and_port(
        self,
        config_path: pathlib.Path,
        local_port: int,
        description: str,
    ):
        self.configure_upnp(config_path)
        public_ip, public_port = self.get_public_ip_and_port(
            config_path, local_port, description,
        )
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({}))
        config = json.loads(config_path.read_text())
        config['public_ip'] = public_ip
        config['public_port'] = public_port
        config_path.write_text(json.dumps(config, indent=2))

    def get_public_ip_and_port(
        self,
        config_path: pathlib.Path,
        local_port: int,
        description: str = 'dist_calc port mapping',
    ) -> tuple[ipaddress.IPv4Address, int]:
        local_ip = self.get_local_ip()
        if self.upnp_used(config_path):
            public_ip = self.get_public_ip()
            public_port = self.get_free_public_port()
            self.set_rule(
                local_ip=local_ip,
                local_port=local_port,
                public_port=public_port,
                description=description,
            )
            return public_ip, public_port
        return self.get_public_ip_and_port_from_config(config_path)

    def configure_public_ip(self, config_path: pathlib.Path):
        upnp_used = self.upnp_used(config_path)
        if upnp_used:
            self.configure_upnp(config_path)

    @staticmethod
    def upnp_used(config_path: pathlib.Path) -> bool:
        if not config_path.exists():
            return True
        config: dict = json.loads(config_path.read_text())
        return config.get('use_upnp', True)

    @staticmethod
    def configure_upnp(config_path: pathlib.Path):
        if config_path.exists():
            config: dict = json.loads(config_path.read_text())
            config['use_upnp'] = True
        else:
            config = {'use_upnp': True}
        config_path.write_text(json.dumps(config, indent=2))

    @staticmethod
    def get_public_ip_and_port_from_config(
        config_path: pathlib.Path,
    ) -> tuple[ipaddress.IPv4Address, int]:
        config = json.loads(config_path.read_text())
        assert 'public_ip' in config
        assert 'public_port' in config
        return (
            ipaddress.IPv4Address(config['public_ip']),
            int(config['public_port']),
        )
