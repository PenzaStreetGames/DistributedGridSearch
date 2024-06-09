from typing import Iterable, Optional
import uuid

import sqlalchemy as sql

import src.common.backend.db as database
import src.node_controller.models.core as core
import src.node_controller.models.db as db_models


class NodeRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Node):
        with self.db.create_session() as session:
            node: db_models.Node = db_models.Node.from_core(entity)
            session.add(node)
            session.commit()

    def delete_entity(self, uid: uuid.UUID):
        with self.db.create_session() as session:
            node: Optional[db_models.Node] = session.query(
                db_models.Node
            ).where(db_models.Node.node_uid == str(uid)).first()
            if node is not None:
                session.delete(node)
                session.commit()

    def update_entity(self, entity: core.Node):
        with self.db.create_session() as session:
            node = db_models.Node.from_core(entity)
            stmt = sql.update(
                db_models.Node
            ).where(
                db_models.Node.node_uid == node.node_uid
            ).values(
                ipv4_address=node.ipv4_address,
                port=node.port,
                role=node.role,
                status=node.status,
                last_ping=node.last_ping,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, uid: uuid.UUID) -> core.Node:
        with self.db.create_session() as session:
            node: Optional[db_models.Node] = session.query(
                db_models.Node
            ).where(db_models.Node.node_uid == str(uid)).first()
            if node is None:
                raise Exception(f'node with uid {uid} does not exists')
            return node.to_core()

    def get_entities(
        self,
        role: Optional[core.NodeRole] = None,
        status: Optional[core.NodeStatus] = None,
    ) -> Iterable[core.Node]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Node)
            if role is not None:
                stmt = stmt.where(db_models.Node.role == role.value)
            if status is not None:
                stmt = stmt.where(db_models.Node.status == status.value)
            nodes = session.scalars(stmt).all()
        return [node.to_core() for node in nodes]

    def upsert_entity(self, entity: core.Node):
        with self.db.create_session() as session:
            node: Optional[db_models.Node] = session.query(
                db_models.Node
            ).where(
                db_models.Node.node_uid == str(entity.node_uid)
            ).first()
        if node is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)

