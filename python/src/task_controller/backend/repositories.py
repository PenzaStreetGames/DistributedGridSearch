from typing import Optional, Iterable
import uuid
import sqlalchemy as sql

import src.common.backend.db as database
import src.task_controller.models.core as core
import src.task_controller.models.db as db_models


class SubtaskRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Subtask):
        with self.db.create_session() as session:
            subtask = db_models.Subtask.from_core(entity)
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
                task_uid=subtask.task_uid,
                subtask_type=subtask.subtask_type,
                executor_uid=subtask.executor_uid,
                status=subtask.status,
                created_at=subtask.created_at,
                finished_at=subtask.finished_at,
                params=subtask.params,
                result=subtask.result,
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

    def upsert_entity(self, entity: core.Subtask):
        with self.db.create_session() as session:
            subtask: Optional[db_models.Subtask] = session.query(
                db_models.Subtask
            ).where(
                db_models.Subtask.subtask_uid == str(entity.subtask_uid)
            ).first()
        if subtask is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)


class TaskRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Task):
        with self.db.create_session() as session:
            task = db_models.Task.from_core(entity)
            session.add(task)
            session.commit()

    def delete_entity(self, task_uid: uuid.UUID):
        with self.db.create_session() as session:
            task: Optional[db_models.Task] = session.query(
                db_models.Task,
            ).where(db_models.Task.task_uid == str(task_uid)).first()
            if task is not None:
                session.delete(task)
                session.commit()

    def update_entity(self, entity: core.Task):
        with self.db.create_session() as session:
            task = db_models.Task.from_core(entity)
            stmt = sql.update(
                db_models.Task,
            ).where(
                db_models.Task.task_uid == task.task_uid,
            ).values(
                task_type=task.task_type,
                creator_uid=task.creator_uid,
                status=task.status,
                dataset_uid=task.dataset_uid,
                created_at=task.created_at,
                finished_at=task.finished_at,
                params=task.params,
                result=task.result,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, task_uid: uuid.UUID) -> Optional[core.Task]:
        with self.db.create_session() as session:
            task: Optional[db_models.Task] = session.query(
                db_models.Task
            ).where(db_models.Task.task_uid == str(task_uid)).first()
            if task is None:
                return None
            return task.to_core()

    def get_entities(self) -> Iterable[core.Task]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Task)
            tasks = session.scalars(stmt).all()
        return [task.to_core() for task in tasks]

    def upsert_entity(self, entity: core.Task):
        with self.db.create_session() as session:
            task: Optional[db_models.Task] = session.query(
                db_models.Task
            ).where(
                db_models.Task.task_uid == str(entity.task_uid)
            ).first()
        if task is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)
