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
from models.common_model import ImageRequest, TextValue, ProductAttributes

from google.cloud.ml.applied.images import image_to_text

router = APIRouter()


@router.post("/api/v1/genai/images/attributes")
def generate_attributes(image_request: ImageRequest) -> ProductAttributes:
    """
    Extracts attributes detected from product's image.
    """
    try:
        response = image_to_text.image_to_attributes(image_request)
    except Exception as e:
        print(f"ERROR: Image Attribute Generation Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return response


@router.post("/api/v1/genai/images/descriptions")
def generate_description(image_request: ImageRequest) -> TextValue:
    """
    Generates a product description from an image of product.
    """
    try:
        response = image_to_text.image_to_product_description(image_request.image)
    except Exception as e:
        print(f"ERROR: Image Description Generation Error: -> {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return response
