from abc import abstractmethod, ABC

from sqlmodel import Session, SQLModel
from sqlalchemy import Engine


class Dao(ABC):
    engine: Engine | None = None

    def __init__(self, engine: Engine):
        self.engine = engine

    @abstractmethod
    def create(self, model: SQLModel):
        pass

    @abstractmethod
    def read(self, model: SQLModel, id: int):
        pass

    @abstractmethod
    def update(self, model: SQLModel):
        pass

    @abstractmethod
    def delete(self, model: SQLModel):
        pass


