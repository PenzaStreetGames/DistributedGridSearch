import ipaddress
from typing import Optional


class ClientBase:
    def __init__(
        self,
        ipv4_address: Optional[ipaddress.IPv4Address] = None,
        port: Optional[int] = None,
    ) -> None:
        self.ipv4_address = ipv4_address
        self.port = port

    def get_server_url(self, path: str) -> str:
        assert self.ipv4_address is not None
        assert self.port is not None
        return f'http://{self.ipv4_address}:{self.port}{path}'

    def set_server(
        self, ipv4_address: ipaddress.IPv4Address, port: int,
    ) -> 'ClientBase':
        self.ipv4_address = ipv4_address
        self.port = port
        return self
