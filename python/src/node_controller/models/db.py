import datetime
import ipaddress
import uuid

import sqlalchemy as sql
import sqlalchemy.orm as orm

import src.node_controller.models.core as core


class Base(orm.DeclarativeBase):
    pass


class Node(Base):
    __tablename__ = 'node'

    node_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True,
    )
    ipv4_address: orm.Mapped[str] = orm.mapped_column(sql.String(21))
    port: orm.Mapped[int] = orm.mapped_column(sql.Integer)
    role: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    last_ping: orm.Mapped[str] = orm.mapped_column(sql.String(23))

    @staticmethod
    def from_core(obj: core.Node) -> 'Node':
        return Node(
            node_uid=str(obj.node_uid),
            ipv4_address=str(obj.ipv4_address),
            port=obj.port,
            last_ping=obj.last_ping.isoformat(timespec='milliseconds'),
            role=obj.role.value,
            status=obj.status.value,
        )

    def to_core(self) -> core.Node:
        return core.Node(
            node_uid=uuid.UUID(self.node_uid),
            ipv4_address=ipaddress.IPv4Address(self.ipv4_address),
            port=self.port,
            last_ping=datetime.datetime.fromisoformat(self.last_ping),
            role=[
                elem for elem in core.NodeRole if elem.value == self.role
            ][0],
            status=[
                elem for elem in core.NodeStatus if elem.value == self.status
            ][0],
        )

    def __repr__(self) -> str:
        return (
            'Node('
            f'node_uid={self.node_uid!r}, '
            f'ipv4_address={self.ipv4_address!r}, '
            f'port={self.port!r}, '
            f'role={self.role!r}, '
            f'status={self.status!r}, '
            f'last_ping={self.last_ping!r})'
        )
