import datetime
import ipaddress
from typing import Optional
import uuid

import sqlalchemy as sql
import sqlalchemy.orm as orm

import src.task_executor.models.core as core


class Base(orm.DeclarativeBase):
    pass


class Subtask(Base):
    __tablename__ = 'subtask'

    subtask_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True,
    )
    creator_uid: orm.Mapped[str] = orm.mapped_column(sql.String(36))
    dataset_uid: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(36))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))
    created_at: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(23))
    finished_at: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(23))

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=str(obj.subtask_uid),
            creator_uid=str(obj.creator_uid),
            dataset_uid=(
                str(obj.dataset_uid) if obj.dataset_uid is not None else None
            ),
            status=obj.status.value,
            created_at=(
                obj.created_at.isoformat(timespec='milliseconds')
                if obj.created_at is not None else None
            ),
            finished_at=(
                obj.finished_at.isoformat(timespec='milliseconds')
                if obj.finished_at is not None else None
            )
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=uuid.UUID(self.subtask_uid),
            creator_uid=uuid.UUID(self.creator_uid),
            dataset_uid=(
                uuid.UUID(str(self.dataset_uid))
                if self.dataset_uid is not None else None
            ),
            status=[
                elem
                for elem in core.SubtaskStatus
                if elem.value == self.status
            ][0],
            created_at=(
                datetime.datetime.fromisoformat(str(self.created_at))
                if self.created_at is not None else None
            ),
            finished_at=(
                datetime.datetime.fromisoformat(str(self.finished_at))
                if self.finished_at is not None else None
            )
        )

    def __repr__(self):
        return (
            'Subtask('
            f'subtask_uid={self.subtask_uid!r}, '
            f'creator_uid={self.creator_uid!r}, '
            f'dataset_uid={self.dataset_uid!r}, '
            f'status={self.status!r}, '
            f'created_at={self.created_at!r}, '
            f'finished_at={self.finished_at!r})'
        )
