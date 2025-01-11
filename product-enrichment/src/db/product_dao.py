from db.dao import Dao
from common.model import  Product
from sqlmodel import Session, SQLModel
from datetime import datetime

class ProductDao(Dao):
    def create(self, model: Product):
        with Session(self.engine) as session:
            model.created = datetime.now()
            model.updated = datetime.now()
            session.add(model)
            session.commit()
            session.refresh(model)
            return model

    def read(self, model: SQLModel, id: int):
        with Session(self.engine) as session:
            return  session.get(model, id)

    def update(self, model: Product):
        with Session(self.engine) as session:

            existing = session.get(Product, model.id)

            existing.updated = datetime.now()
            existing.name = model.name
            existing.sku = model.sku
            existing.category = model.category
            existing.short_description = model.short_description
            existing.long_description = model.long_description

            session.add(existing)
            session.commit()
            session.refresh(existing)
            return model

    def delete(self, model: Product):
        pass