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

import logging

from fastapi import APIRouter, Depends, HTTPException
from auth import (
    AuthenticatedPrincipal,
    ROUTER_AUTH_DEPENDENCIES,
    require_authenticated_principal,
    scope_product_id_for_delete,
    scope_product_id_for_upsert,
    validate_optional_product_image_uri,
    validate_product_categories,
)
from models.common_model import Product, ProductAttributes, MarketingRequest, TextValue
from models.checks_model import Status

from google.cloud.ml.applied.attributes import attributes
from google.cloud.ml.applied.marketing import marketing
from google.cloud.ml.applied.embeddings import search

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=ROUTER_AUTH_DEPENDENCIES)


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
        validated_categories = validate_product_categories(product.category)
        validated_image = validate_optional_product_image_uri(product.image_uri)
        response = attributes.retrieve_and_generate_attributes(
            desc=product.description,
            category=validated_categories,
            image=validated_image,
            base64=False,
            filters=validated_categories,
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid product attribute request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Retrieval & Generation Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
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
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid product marketing request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Marketing Copy Generation Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return response


@router.post("/api/v1/genai/products")
def product_create_index(
    product: Product,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> Status:
    try:
        scoped_id = scope_product_id_for_upsert(
            product.id, principal, is_update=False
        )
        validated_categories = validate_product_categories(product.category)
        validated_image = validate_optional_product_image_uri(product.image_uri)
        search.upsert_dp(
            prod_id=scoped_id,
            desc=product.description,
            image=validated_image,
            cat=validated_categories,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid product create index request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Index Create Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return Status(status="OK")


@router.put("/api/v1/genai/products/{product_id}")
def update_vector_search_index(
    product_id: str,
    product: Product,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> Status:
    """
    Adding the new/updated product info into already built&deployed
        Vector Search Index
    """
    try:
        if product.id is not None and product.id != product_id:
            raise ValueError("Path product_id must match request body product.id")
        scoped_id = scope_product_id_for_upsert(
            product_id, principal, is_update=True
        )
        validated_categories = validate_product_categories(product.category)
        validated_image = validate_optional_product_image_uri(product.image_uri)
        search.upsert_dp(
            prod_id=scoped_id,
            desc=product.description,
            image=validated_image,
            cat=validated_categories,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid product index update request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Index Update Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return Status(status="OK")


@router.delete("/api/v1/genai/products/{product_id}")
def remove_product_from_vector_search(
    product_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> None:
    """
    Removing the product from already built&deployed Vector Search Index

    Params:
    product_id: The unique id of the product.

    Returns:
    If successful, the response body is empty[https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.indexes/removeDatapoints}
    """
    try:
        scoped_id = scope_product_id_for_delete(product_id, principal)
        search.delete_dp(prod_id=scoped_id)
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid product index delete request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Index Delete Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return None
