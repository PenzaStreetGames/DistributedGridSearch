import datetime
import json
from typing import Optional
import uuid

import sqlalchemy as sql
import sqlalchemy.orm as orm

import src.task_controller.models.core as core


class Base(orm.DeclarativeBase):
    pass


class Subtask(Base):
    __tablename__ = 'subtask'

    subtask_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True
    )
    task_uid: orm.Mapped[str] = orm.mapped_column(sql.ForeignKey('task.task_uid'))
    subtask_type: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    executor_uid: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(36))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    created_at: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(23))
    finished_at: orm.Mapped[Optional[str]] = orm.mapped_column(sql.DateTime)
    params: orm.Mapped[Optional[dict]] = orm.mapped_column(sql.Text)
    result: orm.Mapped[Optional[dict]] = orm.mapped_column(sql.Text)

    task: orm.Mapped['Task'] = orm.relationship(back_populates='subtasks')

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=str(obj.subtask_uid),
            task_uid=str(obj.task_uid),
            subtask_type=obj.subtask_type.value,
            executor_uid=str(obj.executor_uid) if obj.executor_uid else None,
            status=obj.status.value,
            created_at=(
                obj.created_at.isoformat(timespec='milliseconds')
                if obj.created_at else obj.created_at
            ),
            finished_at=(
                obj.finished_at.isoformat(timespec='milliseconds')
                if obj.finished_at else obj.finished_at
            ),
            params=(
                json.dumps(obj.params) if obj.params is not None else None
            ),
            result=(
                json.dumps(obj.result) if obj.result is not None else None
            ),
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=uuid.UUID(self.subtask_uid),
            task_uid=uuid.UUID(self.task_uid),
            subtask_type=[
                elem
                for elem in core.SubtaskType
                if elem.value == self.subtask_type
            ][0],
            executor_uid=(
                uuid.UUID(str(self.executor_uid))
                if self.executor_uid else None
            ),
            status=[
                elem
                for elem in core.SubtaskStatus
                if elem.value == self.status
            ][0],
            created_at=(
                datetime.datetime.fromisoformat(str(self.created_at))
                if self.created_at is not None
                else None
            ),
            finished_at=(
                datetime.datetime.fromisoformat(str(self.finished_at))
                if self.finished_at is not None
                else None
            ),
            params=(
                json.loads(str(self.params))
                if self.params is not None
                else None
            ),
            result=(
                json.loads(str(self.result))
                if self.result is not None
                else None
            ),
        )

    def __repr__(self):
        return (
            "Subtask("
            f"subtask_uid={self.subtask_uid!r}, "
            f"task_uid={self.task_uid!r}, "
            f"subtask_type={self.subtask_type!r}, "
            f"executor_uid={self.executor_uid!r}, "
            f"subtask_status={self.status!r}, "
            f"created_at={self.created_at!r}, "
            f"finished_at={self.finished_at!r}, "
            f"params={self.params!r}, "
            f"result={self.result!r})"
        )


class Task(Base):
    __tablename__ = 'task'

    task_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True
    )
    task_type: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    creator_uid: orm.Mapped[str] = orm.mapped_column(sql.String(36))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    dataset_uid: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(36))
    created_at: orm.Mapped[Optional[datetime.datetime]] = orm.mapped_column(
        sql.String(23),
    )
    finished_at: orm.Mapped[Optional[datetime.datetime]] = orm.mapped_column(
        sql.String(23),
    )
    params: orm.Mapped[Optional[dict]] = orm.mapped_column(sql.Text)
    result: orm.Mapped[Optional[dict]] = orm.mapped_column(sql.Text)

    subtasks: orm.Mapped[list['Subtask']] = orm.relationship(
        back_populates='task',
    )

    @staticmethod
    def from_core(obj: core.Task) -> 'Task':
        return Task(
            task_uid=str(obj.task_uid),
            task_type=obj.task_type.value,
            creator_uid=str(obj.creator_uid),
            status=obj.status.value,
            dataset_uid=(
                str(obj.dataset_uid) if obj.dataset_uid is not None else None
            ),
            created_at=(
                obj.created_at.isoformat(timespec='milliseconds')
                if obj.created_at is not None else None
            ),
            finished_at=(
                obj.finished_at.isoformat(timespec='milliseconds')
                if obj.finished_at is not None else None
            ),
            params=(
                json.dumps(obj.params) if obj.params is not None else None
            ),
            result=(
                json.dumps(obj.result) if obj.result is not None else None
            ),
        )

    def to_core(self) -> core.Task:
        return core.Task(
            task_uid=uuid.UUID(self.task_uid),
            task_type=[
                elem
                for elem in core.TaskType
                if elem.value == self.task_type
            ][0],
            creator_uid=uuid.UUID(self.creator_uid),
            dataset_uid=(
                uuid.UUID(str(self.dataset_uid))
                if self.dataset_uid is not None else None
            ),
            status=[
                elem
                for elem in core.TaskStatus
                if elem.value == self.status
            ][0],
            created_at=(
                datetime.datetime.fromisoformat(str(self.created_at))
                if self.created_at is not None else None
            ),
            finished_at=(
                datetime.datetime.fromisoformat(str(self.finished_at))
                if self.finished_at is not None else None
            ),
            params=(
                json.loads(str(self.params))
                if self.params is not None else None
            ),
            result=(
                json.loads(str(self.result))
                if self.result is not None else None
            ),
            subtasks=[subtask.to_core() for subtask in self.subtasks],
        )

    def __repr__(self):
        return (
            "Task("
            f"task_uid={self.task_uid!r}, "
            f"type={self.task_type!r}, "
            f"creator_uid={self.creator_uid!r}, "
            f"status={self.status!r}, "
            f"dataset_uid={self.dataset_uid!r}, "
            f"created_at={self.created_at!r}, "
            f"finished_at={self.finished_at!r}, "
            f"params={self.params!r}, "
            f"result={self.result!r})"
        )
