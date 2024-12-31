#   Copyright 2022 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from datetime import datetime

from sqlalchemy import Engine

from common.model import Product
from sqlmodel import Session
from fastapi import status, Response, FastAPI

def register(app: FastAPI, engine: Engine):
    @app.post("/products", status_code=status.HTTP_201_CREATED)
    def create_product(product: Product):
        with Session(engine) as session:
            product.created = datetime.now()
            product.updated = datetime.now()
            session.add(product)
            session.commit()
            session.refresh(product)
            return product

    @app.put("/products/:product_id", status_code=status.HTTP_202_ACCEPTED)
    def update_product(product_id: int, product: Product, response: Response):

        with Session(engine) as session:
            if product_id == product.id:
                existing = session.get(Product, product_id)

                existing.updated = datetime.now()
                existing.name = product.name
                existing.sku = product.sku
                existing.category = product.category
                existing.short_description = product.short_description
                existing.long_description = product.long_description

                session.add(existing)
                session.commit()
                session.refresh(existing)
                return product
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return None

    @app.get("/products/:product_id", status_code=status.HTTP_200_OK)
    def get_product(product_id: int, response: Response):
        with Session(engine) as session:
            product = session.get(Product, product_id)
            if product is not None:
                return product
            else:
                response.status_code = status.HTTP_404_NOT_FOUND
                return None