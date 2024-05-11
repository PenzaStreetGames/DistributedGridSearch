import sqlalchemy as sql
import sqlalchemy.orm as orm
from typing import Type
from typing import Optional

import src.node_controller.models.db as db_models


class DB:
    def __init__(self, db_name: str, base: Type[orm.DeclarativeBase]):
        self.db_name = db_name
        self.base = base
        self.engine: Optional[sql.Engine] = None
        self.session: Optional[orm.Session] = None

    def create_session(self) -> orm.Session:
        if not self.engine:
            self.engine = sql.create_engine(
                f'sqlite:///{self.db_name}', echo=True,
            )
            self.base.metadata.create_all(self.engine)
            self.session = orm.sessionmaker(
                self.engine, expire_on_commit=False
            )
        return self.session()

    def drop_database(self):
        self.base.metadata.drop_all(self.engine)
