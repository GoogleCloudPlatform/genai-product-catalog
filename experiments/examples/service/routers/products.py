# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi import APIRouter, HTTPException
from models.common_model import Product, ProductAttributes, MarketingRequest, TextValue
from models.checks_model import Status

from google.cloud.ml.applied.attributes import attributes
from google.cloud.ml.applied.marketing import marketing
from google.cloud.ml.applied.embeddings import search

router = APIRouter()


@router.post("/api/v1/genai/products/attributes")
def suggest_attributes(product: Product) -> ProductAttributes:
    """
    Uses Vertex AI to create attribute suggestions for product.

    ## Attributes
    Are a one (product) to many attribute relationship that allows for
    better searching and categorization. Attributes are generally defined
    at the category level, then inherited by a product belonging to that
    category. This is done to make the shopping experience consistent for
    the customer.

    """
    try:
        response = attributes.retrieve_and_generate_attributes(
            desc=product.description,
            category=product.category,
            image=product.image_uri,
            base64=False,
            filters=product.category,
        )
    except Exception as e:
        print(f"ERROR: Product Retrieval & Generation Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return response


@router.post("/api/v1/genai/products/marketing")
def generate_marketing_copy(marketing_request: MarketingRequest) -> TextValue:
    """
    Generate Marketing Copy for a product based on its description, image and/or
    categories.
    """
    try:
        response = marketing.generate_marketing_copy(marketing_request)
    except Exception as e:
        print(f"ERROR: Product Marketing Copy Generation Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return response


@router.post("/api/v1/genai/products")
def product_create_index(product: Product) -> Status:
    try:
        search.upsert_dp(
            prod_id=product.id,
            desc=product.description,
            image=product.image_uri,
            cat=product.category,
        )

    except Exception as e:
        print(f"ERROR: Product Index Create Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return Status(status="OK")


@router.put("/api/v1/genai/products/{product_id}")
def update_vector_search_index(product_id: str, product: Product) -> Status:
    """
    Adding the new/updated product info into already built&deployed
        Vector Search Index
    """
    try:
        search.upsert_dp(
            prod_id=product.id,
            desc=product.description,
            image=product.image_uri,
            cat=product.category,
        )

    except Exception as e:
        print(f"ERROR: Product Index Update Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return Status(status="OK")


@router.delete("/api/v1/genai/products/{product_id}")
def remove_product_from_vector_search(product_id: str) -> None:
    """
    Removing the product from already built&deployed Vector Search Index

    Params:
    product_id: The unique id of the product.

    Returns:
    If successful, the response body is empty[https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.indexes/removeDatapoints}
    """
    try:
        search.delete_dp(prod_id=product_id)
    except Exception as e:
        print(f"ERROR: Product Index Delete Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return None
