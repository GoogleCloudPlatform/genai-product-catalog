#  Copyright 2023 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from typing import Optional
from pydantic import BaseModel


class CategoryList(BaseModel):
    values: list[list[str]] = []


class Product(BaseModel):
    id: str | None
    description: str
    category: Optional[list[str]] = []
    image_uri: Optional[str] = None


class ImageRequest(BaseModel):
    image: str


class AttributeValue(BaseModel):
    attribute_name: str
    attribute_value: str | list[str]


class ProductAttributes(BaseModel):
    product_attributes: list[AttributeValue] = []


class MarketingRequest(BaseModel):
    description: str
    attributes: list[AttributeValue]


class TextValue(BaseModel):
    text: str


class Status(BaseModel):
    status: str


class Liveliness(BaseModel):
    message: str


def parse_project_attributes_from_dict(obj: dict) -> ProductAttributes:
    out = ProductAttributes()

    for k in obj.keys():
        out.product_attributes.append(
            AttributeValue(attribute_name=k, attribute_value=obj[k])
        )
    return out


def parse_list_to_dict(obj: list) -> dict:
    prod_dict = {}

    for i in obj:
        key = i["name"]
        value = i["value"]
        prod_dict[key] = value

    return prod_dict


def attribute_values_to_dict(values: list[AttributeValue]) -> dict[str, str]:
    out: dict[str, str] = {}
    for a in values:
        out[a.attribute_name] = a.attribute_value

    return out


def dict_to_attribute_values(values: dict[str, str]) -> list[AttributeValue]:
    out = []
    for key in values:
        out.append(AttributeValue(attribute_name=key, attribute_value=values[key]))

    return out
