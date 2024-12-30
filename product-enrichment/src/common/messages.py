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
from optparse import Option
from typing import Optional, Any

from pydantic import BaseModel
from enum import StrEnum, auto

class Behavior(StrEnum):
    USE_ATTACHED_IMAGES = auto()
    USE_ATTACHED_VIDEOS = auto()
    USE_GOOGLE_GROUNDING = auto()
    USE_CRITIC = auto()

class Step(StrEnum):
    ALL = auto()
    PRODUCT_DESCRIPTION = auto()
    PRODUCT_ATTRIBUTES = auto()
    SUGGEST_ADDITIONAL_ATTRIBUTES = auto()
    SUGGEST_ADDITIONAL_CATEGORIES = auto()
    GENERATE_IMAGES = auto()

class ImageGenPrompt(BaseModel):
    count: int
    prompt: str

class Router(BaseModel):
    category_meta_key: str = "categories"
    category_meta_delimiter_key: str = "category_delimiter"
    behaviors: list[Behavior] = []
    steps: list[Step] = []
    image_gen_prompts: Optional[list[ImageGenPrompt]] = []

class Image(BaseModel):
    url: str
    mime_type: str

class Meta:
    key: str
    values: list[Any]

class MapperHint(BaseModel):
    json_path: str
    target_path: str
    description: str


class AttributeValueType(StrEnum):
    STRING = auto()
    NUMBER = auto()
    DATE = auto()
    BOOLEAN = auto()
    LIST_OF_STRINGS = auto()
    LIST_OF_NUMBERS = auto()


class AttributeConstraint(BaseModel):
    name: str
    is_required: bool = True
    is_list: Optional[bool] = False
    category_id: Optional[str]
    value_type: Optional[AttributeValueType] = AttributeValueType.STRING
    min_value: Optional[float] = 0.0
    max_value: Optional[float] = 0.0
    min_length: Optional[int] = 1
    max_length: Optional[int] = 64
    constrained_values: list[Any] = []
    default_value: Optional[Any]


class RoutingSlip(BaseModel):
    """
    Is used to determine and/or override the default workflow of any given product.
    for a single product. Each product is wrapped in a routing slip used to experiment
    and route product information effectively.
    """
    router: Optional[Router] = None
    images: list[Image]
    json_product: Any
    product_hints: Optional[list[MapperHint]] = []
    attribute_constraints: Optional[list[AttributeConstraint]] = []
    meta: Optional[list[Meta]] = []


class Category(BaseModel):
    id: str
    name: str
    description: str
    parent_id: Optional[str]


class GlobalConfig(BaseModel):
    """The global config is used to set up for common repeated context values that have a slower rate of change.
    this allows for individual messages routes to be less complex and extended only in times
    of override.
    The vendor name will be used if a vendor specific configuration is present, this
    is intended to allow multiple market-place and/or partners to create custom rules
    for processing. Once a vendor rule set is processed, then the default ruleset will
    be processed, if no vendor specific rules are present, then only the default will be
    executed"""
    name: Optional[str] = "default"
    router: Router
    vendor_name: Optional[str] = None
    vendor_meta_key = Optional[str] = "vendor"
    categories: list[Category]
    attribute_constraints: list[AttributeConstraint]
