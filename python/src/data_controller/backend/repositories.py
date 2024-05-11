from typing import Iterable
from typing import Optional
import uuid

import sqlalchemy as sql

import src.common.backend.db as database
import src.data_controller.models.core as core
import src.data_controller.models.db as db_models


class DatasetRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Dataset):
        with self.db.create_session() as session:
            image: db_models.Dataset = db_models.Dataset.from_core(entity)
            session.add(image)
            session.commit()

    def delete_entity(self, dataset_uid: uuid.UUID):
        with self.db.create_session() as session:
            dataset: Optional[db_models.Dataset] = session.query(
                db_models.Dataset,
            ).where(db_models.Dataset.dataset_uid == str(dataset_uid)).first()
            if dataset is not None:
                session.delete(dataset)
                session.commit()

    def update_entity(self, entity: core.Dataset):
        with self.db.create_session() as session:
            dataset = db_models.Dataset.from_core(entity)
            stmt = sql.update(
                db_models.Dataset,
            ).where(
                db_models.Dataset.dataset_uid == dataset.dataset_uid,
            ).values(
                magnet_link=dataset.magnet_link,
                path=dataset.path,
                status=dataset.status,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, dataset_uid: uuid.UUID) -> Optional[core.Dataset]:
        with self.db.create_session() as session:
            dataset: Optional[db_models.Dataset] = session.query(
                db_models.Dataset
            ).where(db_models.Dataset.dataset_uid == str(dataset_uid)).first()
            if dataset is None:
                return None
            return dataset.to_core()

    def get_entities(self) -> Iterable[core.Dataset]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Dataset)
            datasets = session.scalars(stmt).all()
        return [dataset.to_core() for dataset in datasets]

    def upsert_entity(self, entity: core.Dataset):
        with self.db.create_session() as session:
            image: Optional[db_models.Dataset] = session.query(
                db_models.Dataset
            ).where(
                db_models.Dataset.dataset_uid == str(entity.dataset_uid)
            ).first()
        if image is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)
