import datetime
import ipaddress
import pytest
import uuid

import src.node_controller.models.core as core
import src.node_controller.models.db as db
import src.node_controller.models.web as web

CONST_UUID = 'b5b9018f-92c1-4932-8cb8-a2cb4483aee4'
CONST_DATETIME = '2024-05-05T12:47:39.651'
CONST_IP_ADDRESS = '127.0.0.1'


@pytest.mark.parametrize(
    "role, status",
    [
        pytest.param(
            core.NodeRole.EXECUTOR, core.NodeStatus.ACTIVE,
        ),
        pytest.param(
            core.NodeRole.CREATOR, core.NodeStatus.INACTIVE,
        ),
        pytest.param(
            core.NodeRole.REGISTRY, core.NodeStatus.UNKNOWN,
        ),
    ],
)
def test_node_info_model_core_db_conversion(
    role: core.NodeRole, status: core.NodeStatus,
):
    core_model = core.Node(
        node_uid=uuid.UUID(CONST_UUID),
        ipv4_address=ipaddress.IPv4Address(CONST_IP_ADDRESS),
        port=55555,
        role=role,
        status=status,
        last_ping=datetime.datetime.fromisoformat(CONST_DATETIME),
    )
    db_model = db.Node(
        node_uid=CONST_UUID,
        ipv4_address=CONST_IP_ADDRESS,
        port=55555,
        role=role.value,
        status=status.value,
        last_ping=CONST_DATETIME,
    )
    db_mapped_model = db.Node.from_core(core_model)
    assert db_mapped_model.node_uid == db_model.node_uid
    assert db_mapped_model.ipv4_address == db_model.ipv4_address
    assert db_mapped_model.port == db_model.port
    assert db_mapped_model.role == db_model.role
    assert db_mapped_model.status == db_model.status
    assert db_mapped_model.last_ping == db_model.last_ping
    core_mapped_model = db_mapped_model.to_core()
    assert core_mapped_model == core_model


@pytest.mark.parametrize(
    "role, status",
    [
        pytest.param(
            core.NodeRole.EXECUTOR, core.NodeStatus.ACTIVE,
        ),
        pytest.param(
            core.NodeRole.CREATOR, core.NodeStatus.INACTIVE,
        ),
        pytest.param(
            core.NodeRole.REGISTRY, core.NodeStatus.UNKNOWN,
        ),
    ],
)
def test_node_info_model_core_web_conversion(
    role: core.NodeRole, status: core.NodeStatus,
):
    core_model = core.Node(
        node_uid=uuid.UUID(CONST_UUID),
        ipv4_address=ipaddress.IPv4Address(CONST_IP_ADDRESS),
        port=55555,
        role=role,
        status=status,
        last_ping=datetime.datetime.fromisoformat(CONST_DATETIME),
    )
    web_model = web.Node(
        node_uid=CONST_UUID,
        ipv4_address=CONST_IP_ADDRESS,
        port=55555,
        role=role.value,
        status=status.value,
        last_ping=CONST_DATETIME,
    )
    mapped_web_model = web.Node.from_core(core_model)
    assert mapped_web_model == web_model
    mapped_core_model = mapped_web_model.to_core()
    assert mapped_core_model == core_model
