from typing import Iterable
from typing import Optional
import uuid

import sqlalchemy as sql

import src.common.backend.db as database
import src.env_controller.models.core as core
import src.env_controller.models.db as db_models


class ImageRepository:
    def __init__(self, db: database.DB):
        self.db = db

    def create_entity(self, entity: core.Image):
        with self.db.create_session() as session:
            image: db_models.Image = db_models.Image.from_core(entity)
            session.add(image)
            session.commit()

    def delete_entity(self, image_tag: str):
        with self.db.create_session() as session:
            image: Optional[db_models.Image] = session.query(
                db_models.Image,
            ).where(db_models.Image.image_tag == image_tag).first()
            if image is not None:
                session.delete(image)
                session.commit()

    def update_entity(self, entity: core.Image):
        with self.db.create_session() as session:
            image = db_models.Image.from_core(entity)
            stmt = sql.update(
                db_models.Image,
            ).where(
                db_models.Image.image_tag == image.image_tag,
            ).values(
                image_id=image.image_id,
                status=image.status,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, image_tag: str) -> Optional[core.Image]:
        with self.db.create_session() as session:
            image: Optional[db_models.Image] = session.query(
                db_models.Image
            ).where(db_models.Image.image_tag == image_tag).first()
            if image is None:
                raise Exception(f'image with tag {image_tag} does not exists')
            return image.to_core()

    def get_entities(self) -> Iterable[core.Image]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Image)
            images = session.scalars(stmt).all()
        return [image.to_core() for image in images]

    def upsert_entity(self, entity: core.Image):
        with self.db.create_session() as session:
            image: Optional[db_models.Image] = session.query(
                db_models.Image
            ).where(db_models.Image.image_tag == entity.image_tag).first()
        if image is None:
            self.create_entity(entity)
        else:
            self.update_entity(entity)


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
                image_tag=subtask.image_tag,
                container_id=subtask.container_id,
                status=subtask.status,
            )
            session.execute(stmt)
            session.commit()

    def get_entity(self, subtask_uid: uuid.UUID) -> core.Subtask:
        with self.db.create_session() as session:
            subtask: Optional[db_models.Subtask] = session.query(
                db_models.Subtask
            ).where(db_models.Subtask.subtask_uid == str(subtask_uid)).first()
            if subtask is None:
                raise Exception(
                    f'subtask with uid {subtask_uid} does not exists',
                )
            return subtask.to_core()

    def get_entities(self) -> Iterable[core.Subtask]:
        with self.db.create_session() as session:
            stmt = sql.select(db_models.Subtask)
            subtasks = session.scalars(stmt).all()
        return [subtask.to_core() for subtask in subtasks]
