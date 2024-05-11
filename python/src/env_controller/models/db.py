from typing import Optional
import uuid

import sqlalchemy as sql
import sqlalchemy.orm as orm

import src.env_controller.models.core as core


class Base(orm.DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = 'image'

    image_tag: orm.Mapped[str] = orm.mapped_column(
        sql.String(256), primary_key=True,
    )
    image_id: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(71))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))

    subtasks: orm.Mapped[list['Subtask']] = orm.relationship(
        back_populates='image',
    )

    @staticmethod
    def from_core(obj: core.Image) -> 'Image':
        return Image(
            image_tag=obj.image_tag,
            image_id=obj.image_id,
            status=obj.status.value,
        )

    def to_core(self) -> core.Image:
        return core.Image(
            image_tag=self.image_tag,
            image_id=self.image_id,
            status=[
                elem for elem in core.ImageStatus if elem.value == self.status
            ][0],
        )

    def __repr__(self):
        return (
            "Image("
            f"image_tag={self.image_tag!r}, "
            f"image_id={self.image_id!r}, "
            f"status={self.status!r})"
        )


class Subtask(Base):
    __tablename__ = 'subtask'

    subtask_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True
    )
    image_tag: orm.Mapped[str] = orm.mapped_column(
        sql.ForeignKey('image.image_tag'),
    )
    container_id: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(64))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))

    image: orm.Mapped['Image'] = orm.relationship(back_populates='subtasks')

    @staticmethod
    def from_core(obj: core.Subtask) -> 'Subtask':
        return Subtask(
            subtask_uid=str(obj.subtask_uid),
            image_tag=obj.image.image_tag,
            # image=Image.from_core(obj.image),
            container_id=obj.container_id,
            status=obj.status.value,
        )

    def to_core(self) -> core.Subtask:
        return core.Subtask(
            subtask_uid=uuid.UUID(self.subtask_uid),
            image=self.image.to_core(),
            container_id=self.container_id,
            status=[
                elem
                for elem in core.SubtaskStatus
                if elem.value == self.status
            ][0],
        )

    def __repr__(self):
        return (
            "Subtask("
            f"subtask_uid={self.subtask_uid!r}, "
            f"image_tag={self.image_tag!r}, "
            f"container_id={self.container_id!r}, "
            f"status={self.status!r})"
        )
