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

import json
import logging

from fastapi import APIRouter, HTTPException
from models.common_model import ImageRequest, TextValue, ProductAttributes

from google.cloud.ml.applied.images import image_to_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/v1/genai/images/attributes")
def generate_attributes(image_request: ImageRequest) -> ProductAttributes:
    """
    Extracts attributes detected from product's image.
    """
    try:
        response = image_to_text.image_to_attributes(image_request)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to decode image attribute model output: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    except ValueError as e:
        logger.warning("Invalid image attribute request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Image Attribute Generation Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return response


@router.post("/api/v1/genai/images/descriptions")
def generate_description(image_request: ImageRequest) -> TextValue:
    """
    Generates a product description from an image of product.
    """
    try:
        response = image_to_text.image_to_product_description(image_request.image)
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid image description request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Image Description Generation Error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        return response
