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


import http.client
import json
import typing
import urllib.request

from google.cloud.ml.applied.model import domain_model as m
from google.cloud.ml.applied.utils import utils
from vertexai.preview.generative_models import Image, Part

multimodal_model = utils.get_gemini_pro_vision()


def get_image_bytes_from_url(image_url: str) -> bytes:
    with urllib.request.urlopen(image_url) as response:
        response = typing.cast(http.client.HTTPResponse, response)
        image_bytes = response.read()
    return image_bytes


def load_image_from_url(image_url: str) -> Image:
    image_bytes = get_image_bytes_from_url(image_url)
    return Image.from_bytes(image_bytes)


# works only with public image
def get_url_from_gcs(gcs_uri: str) -> str:
    # converts gcs uri to url for image display.
    url = "https://storage.googleapis.com/" + gcs_uri.replace("gs://", "").replace(
        " ", "%20"
    )
    return url


def from_url(image: str):
    image = load_image_from_url(image)  # convert to bytes
    return image


def from_gsc_uri(image_uri):
    # print(image_uri)
    image_part = Part.from_uri(image_uri, mime_type="image/jpeg")
    return image_part


def content_generation(prompt: str, im):
    responses = ""
    try:
        responses = multimodal_model.generate_content(
            contents=[prompt, im],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
            },
        )
    except Exception as e:
        print(e)
    return responses


def image_to_attributes(req: m.ImageRequest) -> m.ProductAttributes:
    prompt = """Provide the list of all the product attributes for the main
    product in the image in JSON format"""

    if req.image.startswith("gs://"):
        im = from_gsc_uri(req.image)
    else:
        im = from_url(req.image)

    responses = content_generation(prompt, im)
    res = responses.text
    res = res.replace("```", "")
    res = res.replace("json", "")

    # This produces multiple models, NOT USEFUL for API calls.
    # had to create a parser to return consistent values

    attributes_json = json.loads(res.strip())
    print(attributes_json)

    if "product_attributes" not in attributes_json:
        print("parsing")
        response = m.parse_project_attributes_from_dict(attributes_json)
    else:
        # response = m.parse_list_to_dict(attributes_json.get('product_attributes'))
        response = m.parse_project_attributes_from_dict(
            attributes_json.get("product_attributes")
        )

    return response


def image_to_product_description(image: str) -> m.TextValue:
    prompt = """Write enriched product description for the main product in
    the image for retailer's product catalog"""

    if image.startswith("gs://"):
        im = from_gsc_uri(image)
    else:
        im = from_url(image)
    responses = content_generation(prompt, im)
    res = ""
    for response in responses:
        res += response.candidates[0].content.parts[0].text
    desc = res.strip()

    return m.TextValue(text=desc)
