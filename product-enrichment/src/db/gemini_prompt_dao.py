

from db.dao import Dao
from common.cor import GeminiPromptCommand
from sqlmodel import Session, select
from datetime import datetime

class GeminiPromptsDao(Dao):
    def create(self, model: GeminiPromptCommand):
        with Session(self.engine) as session:
            model.created = datetime.now()
            model.effective = datetime.now()
            session.add(model)
            session.commit()
            session.refresh(model)
            return model

    def read(self, model: GeminiPromptCommand, id: int):
        with Session(self.engine) as session:
            return session.get(GeminiPromptCommand, id)


    def update(self, model: GeminiPromptCommand):
        with Session(self.engine) as session:
            existing = session.get(GeminiPromptCommand, id)
            existing.effective = datetime.now()
            existing.name = model.name
            existing.prompt = model.prompt
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

    def delete(self, model: GeminiPromptCommand):
        with Session(self.engine) as session:
            session.delete(model)
            session.commit()
            return model

    def find_by_name(self, name: str):
        with Session(self.engine) as session:
            statement = select(GeminiPromptCommand).where(GeminiPromptCommand.name == name, GeminiPromptCommand.deleted == None)
            results = session.exec(statement)
            return results.first()