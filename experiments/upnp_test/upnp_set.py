import logging
import socket

import upnpclient


REMOTE_PORT = 55505

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_global_ip(device) -> str:
    service = device.WANIPConn1
    return service.GetExternalIPAddress()['NewExternalIPAddress']


def get_device():
    return upnpclient.discover()[0]


def add_mapping(device, port: int) -> None:
    local_ip = get_local_ip()
    global_ip = get_global_ip(device)
    service = device.WANIPConn1
    service.AddPortMapping(
        NewRemoteHost='',
        NewExternalPort=REMOTE_PORT,
        NewProtocol='TCP',
        NewInternalPort=port,
        NewInternalClient=local_ip,
        NewEnabled='1',
        NewPortMappingDescription='Test port mapping entry from UPnPy.',
        NewLeaseDuration=0
    )
    print(
        f'create mapping {local_ip}:{port} -> {global_ip}:{REMOTE_PORT}'
    )


def delete_mapping(device, port: int) -> None:
    local_ip = get_local_ip()
    global_ip = get_global_ip(device)
    service = device.WANIPConn1
    service.DeletePortMapping(
        NewRemoteHost='',
        NewExternalPort=REMOTE_PORT,
        NewProtocol='TCP',
    )
    print(
        f'remove mapping {local_ip}:{port} -> {global_ip}:{REMOTE_PORT}'
    )


def main() -> None:
    # print(get_local_ip())
    device = get_device()
    # add_mapping(device, 8000)
    delete_mapping(device, 8000)


if __name__ == '__main__':
    main()
