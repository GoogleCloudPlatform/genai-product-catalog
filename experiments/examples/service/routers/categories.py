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

from fastapi import APIRouter, HTTPException
from models.common_model import Product, CategoryList

from google.cloud.ml.applied.categories import category

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/v1/genai/categories")
def suggest_categories(product: Product) -> CategoryList:
    """
    Suggest categories for product based on the product description
    and image (if present).
    """
    try:
        response = category.retrieve_and_rank(
            desc=product.description,
            image=product.image_uri,
            base64=False,
            filters=product.category,
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid category suggestion request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Product Category Retrieve and Ranking Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

    return response
