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
from fastapi import status, Response, FastAPI

from db.product_dao import ProductDao


def register(app: FastAPI, engine: Engine):
    product_dao = ProductDao(engine)

    @app.post("/products", status_code=status.HTTP_201_CREATED)
    def create_product(product: Product):
        return product_dao.create(product)

    @app.put("/products/:product_id", status_code=status.HTTP_202_ACCEPTED)
    def update_product(product_id: int, product: Product, response: Response):
        if product_id == product.id:
            return product_dao.update(product)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return None

    @app.get("/products/:product_id", status_code=status.HTTP_200_OK)
    def get_product(product_id: int, response: Response):
        product = product_dao.read(Product(),product_id)
        if product is not None:
            return product
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return None