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

import math
import os.path
import random
import re
from typing import List, Optional, Union

import pandas as pd
import spacy
import spacy_cleaner
from spacy_cleaner.processing import removers, replacers, mutators

"""
Is a super simple representation of the Retail Data Model used solely for reading and writing JSON.
 
Normally we would add a reference to the external RDM library, however since this only represents a fraction
of the model it was easier to simply reproduce it in simple classes.
"""

SPEC_MATCH_ONE = re.compile("(.*?)\\[(.*)\\](.*)")
SPEC_MATCH_TWO = re.compile("(.*?)=>\"(.*?)\"(.*?)=>\"(.*?)\"(.*)")
SPACE_CLEANER = re.compile('\s+')
ID_CLEANER = re.compile('[^a-zA-Z ]')

MODEL = spacy.load("en_core_web_sm")

PROC_PIPELINE = spacy_cleaner.Pipeline(
    MODEL,
    replacers.replace_punctuation_token,
    mutators.mutate_lemma_token,
    removers.remove_stopword_token,
)

FILE_COLUMNS = {'uniq_id': 'string',
                'crawl_timestamp': 'string',
                'product_url': 'string',
                'product_name': 'string',
                'product_category_tree': 'string',
                'pid': 'string',
                'retail_price': 'Int32',
                'discounted_price': 'Int32',
                'image': 'string',
                'is_FK_Advantage_product': 'string',
                'description': 'string',
                'product_rating': 'string',
                'overall_rating': 'string',
                'brand': 'string',
                'product_specifications': 'string'}


class RoundingRule:
    """ Represents the rules used for rounding decimal numbers """

    def __init__(self):
        self.relevant_decimal = 5
        self.trim_insignificant_digits = False


class Numeric:
    """ Numeric is a decimal value split to ensure consistent multi-platform storage """
    def __init__(self, whole: int, decimal: int):
        self.whole = whole
        self.decimal = decimal


class Currency:
    def __init__(self, numeric: int):
        numeric = numeric * 3
        d_and_c = numeric / 100
        dec, whole = math.modf(d_and_c)
        self.code = "USD"

        if pd.isna(whole):
            whole = 0

        if pd.isna(dec):
            dec = 0

        self.value = Numeric(int(whole), int(dec))
        self.rounding_rule = RoundingRule()


class Image:
    """ The simplest object structure for an image """

    def __init__(self, url):
        url = url.strip()
        self.origin_url = url
        if url.startswith('http'):
            self.url = url[url.index('/image'):]


class BusinessKey:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class Category:
    def __init__(self, name: str):
        _id = ID_CLEANER.sub('', name)
        _id = SPACE_CLEANER.sub('_', _id)
        self.id = _id.lower()
        self.name = name
        self.children: List["Category"] = []

    def add_child(self, category: "Category"):
        self.children.append(category)


class StringValue:
    def __init__(self, value: str):
        self.value: List[str] = [value]


class TemplateAttributeRule:
    def __init__(self, name: str):
        self.name = name
        self.field_type = "STRING"
        self.required = False
        self.allow_overrides = True


class ProductHeaderAttributeValue:
    def __init__(self, template_attribute_name: str, value: str):
        self.template_attribute_rule = TemplateAttributeRule(template_attribute_name)
        self.string_value = value


class ProductHeader:
    def __init__(self,
                 locale: str,
                 name: str,
                 brand: str,
                 short_description: str,
                 long_description: str,
                 images: List[Image],
                 attribute_values: List[ProductHeaderAttributeValue]):

        if isinstance(long_description, str):
            long_description = re.sub("[\t|\r|\n|\\s+]", " ", long_description)
            long_description = long_description.replace('\u2022', '')

        self.locale = locale
        self.name = name if name is not None and isinstance(name, str) else ''
        self.brand = brand if brand is not None and isinstance(brand, str) else ''
        self.short_description = short_description if short_description is not None and isinstance(short_description,
                                                                                                   str) else ''
        self.long_description = long_description if long_description is not None and isinstance(long_description,
                                                                                                str) else ''
        self.nlp_description = ""
        self.images: List[Image] = images if images is not None else []
        self.attribute_values: List[ProductHeaderAttributeValue] = attribute_values


class Product:
    def __init__(self, header: ProductHeader, base_price: int, category: Category, rating: str):
        self.headers: List[ProductHeader] = []
        self.base_price: Currency = Currency(base_price)
        self.categories: List[Category] = [category]
        self.business_keys: List[BusinessKey] = []
        self.headers.append(header)
        self.image_embedding = List = None
        self.text_embedding = List = None

    def add_business_key(self, key: str, value: str):
        self.business_keys.append(BusinessKey(key, value))


def parse_category(value: str, brand_info: List[str]) -> Union[Category, None]: # Category | None:
    if isinstance(value, str):
        clean_value = value.replace("[\"", "").replace("\"]", "")
        clean_values = [x.strip() for x in clean_value.split(" >> ")]
        parent = Category('')
        current = parent
        for i, v in enumerate(clean_values):
            if not any(x in brand_info for x in v.split(" ")):
                if i == 0:
                    current.name = v
                else:
                    cat = Category(v)
                    current.add_child(cat)
                    current = cat
                if i >= 3:
                    break
        return parent

    return None


def get_product_header_attributes(specification: str) -> List[ProductHeaderAttributeValue]:
    m = SPEC_MATCH_ONE.match(specification)
    out: List[ProductHeaderAttributeValue] = []
    if m is not None and m.group(2) is not None:
        phrase = ''
        for c in m.group(2):
            if c == '}':
                m2 = SPEC_MATCH_TWO.match(phrase)
                if m2 and m2.group(2) is not None and m2.group(4) is not None:
                    out.append(ProductHeaderAttributeValue(m2.group(2), m2.group(4)))
                phrase = ''
            else:
                phrase += c
    return out


def parse_nlp_description(description) -> str:
    if not pd.isnull(description):
        doc = MODEL(description.lower())
        lemmas = []
        for token in doc:
            if token.lemma_ not in lemmas and not token.is_stop and token.is_alpha:
                lemmas.append(token.lemma_)

        return " ".join(lemmas)
    return ""


# uniq_id, crawl_timestamp, product_url, product_name, product_category_tree,
# pid, retail_price, discounted_price, image, is_FK_Advantage_product,
# description,product_rating,overall_rating,brand,product_specifications


def get_image_uri(name: str) -> str:
    if isinstance(name, str) and name is not None:
        uri = name[name.index('/image'):] if name.find('/image') > 0 else name
        return uri
    return 'undefined'


def file_exists(name: str):
    path = '/tmp' + name
    return os.path.isfile(path)


def parse_row(r: pd.DataFrame, pre_process: bool = False) -> Product:
    id = r['uniq_id']
    name = r['product_name']
    description = r['description']
    brand = r['brand']
    categories = r['product_category_tree']
    sku = r['pid']

    base_price = pd.to_numeric(r['retail_price'], errors='coerce')
    images_raw = r['image']
    images = []
    rating = random.randint(1, 5)

    c_overall = random.randint(1, 5)
    overall_rating = c_overall if c_overall >= rating else rating

    base_url = r['product_url']

    if isinstance(images_raw, str):
        images_raw = images_raw.replace("[", "").replace("]", "").replace("\"", '')
        images: List[Image] = [Image(x) for x in images_raw.split(",")]

    # No images, ignore product
    if len(images) == 0:
        return None

    product_specifications = r['product_specifications']

    if not pd.isnull(product_specifications):
        attribute_values = get_product_header_attributes(product_specifications)
    else:
        attribute_values = []

    brand_split = [] if pd.isnull(brand) else brand.split(" ")

    cat = parse_category(categories, brand_split)
    header = ProductHeader('EN_US', name, brand, '', description, images, attribute_values)

    if pre_process:
        header.nlp_description = parse_nlp_description(description)

    product = Product(header, base_price, cat, rating=rating)

    product.add_business_key("SKU", sku)
    product.add_business_key("OID", id)
    product.add_business_key("ORIGIN", base_url)
    product.add_business_key("ORIGIN_OVERALL_RATING", overall_rating)

    return product
