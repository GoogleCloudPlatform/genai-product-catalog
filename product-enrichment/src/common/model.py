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

from typing import Optional, Any

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel, Relationship, Column
from pgvector.sqlalchemy import Vector
from datetime import datetime


class ProductImageLink(SQLModel, table=True):
    __tablename__ = 'product_images'
    product_id: int | None = Field(default=None, foreign_key="product.id", primary_key=True)
    image_id: int | None = Field(default=None, foreign_key="images.id", primary_key=True)


class ProductFeatureImageLink(SQLModel, table=True):
    __tablename__ = 'feature_images'
    product_feature_id: int | None = Field(default=None, foreign_key="features.id", primary_key=True)
    image_id: int | None = Field(default=None, foreign_key="images.id", primary_key=True)


class Image(SQLModel, table=True):
    __tablename__ = 'images'
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    mime_type: str
    alt: str


class Product(SQLModel, table=True):
    __tablename__ = 'product'
    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime = Field(default=datetime.now())
    updated: datetime = Field(default=datetime.now())
    name: str
    sku: str = Field(index=True)
    category: str = Field(default="Other")
    short_description: str
    long_description: Optional[str] = Field(default=None)
    features: list["ProductFeature"] = Relationship()
    specifications: list["ProductSpecification"] = Relationship()
    images: list[Image] = Relationship(link_model=ProductImageLink)


class ProductFeature(SQLModel, table=True):
    __tablename__ = 'features'
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: Optional[str] = Field(default=None)
    product_id: int | None = Field(default=None, foreign_key="product.id")
    product: Product | None = Relationship()
    images: list[Image] = Relationship(link_model=ProductFeatureImageLink)


class ProductSpecification(SQLModel, table=True):
    __tablename__ = 'specifications'
    id: Optional[int] = Field(default=None, primary_key=True)
    category: Optional[str] = Field(default="Other")
    key: str
    value: Optional[str] = Field(default=None)
    product_id: int | None = Field(default=None, foreign_key="product.id")
    product: Product | None = Relationship()


class Review(SQLModel, table=True):
    __tablename__ = 'reviews'
    id: Optional[int] = Field(default=None, primary_key=True)
    verified: bool = Field(default=False)
    sentiment_score: float = Field(default=3)
    title: str
    rating: int
    body: Optional[str] = Field(default=None)
    member: Optional[str] = Field(default=None)
    member_since: Optional[str] = Field(default=None)
    product_id: int | None = Field(default=None, foreign_key="product.id")
    product: Product | None = Relationship()


class Reviews(SQLModel, table=True):
    __tablename__ = 'review_stats'
    id: Optional[int] = Field(default=None, primary_key=True)
    aggregate_score: float = Field(default=0.0)
    product_id: int | None = Field(default=None, foreign_key="product.id")
    product: Product | None = Relationship()


class ProductEmbeddings(SQLModel, table=True):
    __tablename__ = 'embeddings'
    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime = Field(default=datetime.now())
    model_name: str = Field(default="gemini-1.5-flash-002")
    embeddings: Any = Field(sa_column=Column(Vector(768)))
    product_id: int | None = Field(default=None, foreign_key="product.id")
    product: Product | None = Relationship()


class GeminiPrompt(SQLModel, table=True):
    __tablename__ = 'gemini_prompts'
    __table_args__ = (
        UniqueConstraint("name", "effective", name="unique_name_effective"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime = Field(default=datetime.now())
    effective: datetime = Field(default=datetime.now())
    name: str = Field()
    prompt: str = Field()




