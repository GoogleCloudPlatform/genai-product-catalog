

from db.dao import Dao
from common.model import GeminiPrompt
from sqlmodel import Session, select
from datetime import datetime

class GeminiPromptsDao(Dao):
    def create(self, model: GeminiPrompt):
        with Session(self.engine) as session:
            model.created = datetime.now()
            model.effective = datetime.now()
            session.add(model)
            session.commit()
            session.refresh(model)
            return model

    def read(self, model: GeminiPrompt, id: int):
        with Session(self.engine) as session:
            return session.get(GeminiPrompt, id)


    def update(self, model: GeminiPrompt):
        with Session(self.engine) as session:
            existing = session.get(GeminiPrompt, id)
            existing.effective = datetime.now()
            existing.name = model.name
            existing.prompt = model.prompt
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

    def delete(self, model: GeminiPrompt):
        with Session(self.engine) as session:
            session.delete(model)
            session.commit()
            return model

    def find_by_name(self, name: str):
        with Session(self.engine) as session:
            statement = select(GeminiPrompt).where(GeminiPrompt.name == name, GeminiPrompt.effective <= datetime.now()).order_by(GeminiPrompt.effective)
            results = session.exec(statement)
            return results.first()