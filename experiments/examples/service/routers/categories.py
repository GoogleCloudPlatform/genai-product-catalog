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
from models.common_model import Product, CategoryList

from google.cloud.ml.applied.categories import category

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
    except Exception as e:
        print(f"ERROR: Product Category Retrieve and Ranking Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return response
