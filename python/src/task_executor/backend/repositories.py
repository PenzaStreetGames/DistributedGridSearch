from typing import Iterable
from typing import Optional
import uuid

import sqlalchemy as sql

import src.common.backend.db as database
import src.task_executor.models.core as core
import src.task_executor.models.db as db_models


class SubtaskRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Subtask):
        with self.db.create_session() as session:
            subtask: db_models.Subtask = db_models.Subtask.from_core(entity)
            session.add(subtask)
            session.commit()

    def delete_entity(self, subtask_uid: uuid.UUID):
        with self.db.create_session() as session:
            subtask: Optional[db_models.Subtask] = session.query(
                db_models.Subtask,
            ).where(db_models.Subtask.subtask_uid == str(subtask_uid)).first()
            if subtask is not None:
                session.delete(subtask)
                session.commit()

    def update_entity(self, entity: core.Subtask):
        with self.db.create_session() as session:
            subtask = db_models.Subtask.from_core(entity)
            stmt = sql.update(
                db_models.Subtask,
            ).where(
                db_models.Subtask.subtask_uid == subtask.subtask_uid,
            ).values(
                creator_uid=subtask.creator_uid,
                dataset_uid=subtask.dataset_uid,
                status=subtask.status,
                created_at=subtask.created_at,
                finished_at=subtask.finished_at,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, subtask_uid: uuid.UUID) -> Optional[core.Subtask]:
        with self.db.create_session() as session:
            subtask: Optional[db_models.Subtask] = session.query(
                db_models.Subtask
            ).where(db_models.Subtask.subtask_uid == str(subtask_uid)).first()
            if subtask is None:
                return None
            return subtask.to_core()

    def get_entities(self) -> Iterable[core.Subtask]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Subtask)
            subtasks = session.scalars(stmt).all()
        return [subtask.to_core() for subtask in subtasks]


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
            image: Optional[db_models.Node] = session.query(
                db_models.Node
            ).where(db_models.Node.node_uid == entity.node_uid).first()
        if image is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)
