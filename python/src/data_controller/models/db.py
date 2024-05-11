import pathlib
from typing import Optional
import uuid

import sqlalchemy as sql
import sqlalchemy.orm as orm

import src.data_controller.models.core as core


class Base(orm.DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = 'dataset'

    dataset_uid: orm.Mapped[str] = orm.mapped_column(
        sql.String(36), primary_key=True,
    )
    magnet_link: orm.Mapped[Optional[str]] = orm.mapped_column(sql.String(256))
    path: orm.Mapped[str] = orm.mapped_column(sql.String(256))
    status: orm.Mapped[str] = orm.mapped_column(sql.String(64))

    @staticmethod
    def from_core(obj: core.Dataset) -> 'Dataset':
        return Dataset(
            dataset_uid=str(obj.dataset_uid),
            magnet_link=obj.magnet_link,
            path=str(obj.path),
            status=obj.status.value,
        )

    def to_core(self) -> core.Dataset:
        return core.Dataset(
            dataset_uid=uuid.UUID(self.dataset_uid),
            magnet_link=self.magnet_link,
            path=pathlib.Path(self.path),
            status=[
                elem
                for elem in core.DatasetStatus
                if elem.value == self.status
            ][0],
        )

    def __repr__(self) -> str:
        return (
            'Dataset('
            f'dataset_uid={self.dataset_uid!r}, '
            f'magnet_link={self.magnet_link!r}, '
            f'destination={self.path!r}, '
            f'status={self.path!r})'
        )
