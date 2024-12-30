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

"""Functions common to several modules."""
import vertexai
import vertexai.preview

from functools import cache
from typing import Any
from google.cloud import aiplatform_v1
from google.cloud import bigquery
from vertexai.preview.generative_models import GenerativeModel
from google.cloud.ml.applied.config import Config

conf = Config()


@cache
def get_bq_client(project=conf.value(Config.SECTION_PROJECT, "id")):
    return bigquery.Client(project)


@cache
def get_llm():
    vertexai.init(
        project=conf.value(Config.SECTION_PROJECT, "id"),
        location=conf.value(Config.SECTION_PROJECT, "location"),
    )

    return vertexai.language_models.TextGenerationModel.from_pretrained(
        conf.value(Config.SECTION_MODELS, "llm")
    )


@cache
def get_gemini_pro_vision() -> Any:
    multimodal_model = GenerativeModel(conf.value(Config.SECTION_MODELS, "gemini"))

    return multimodal_model


@cache
def get_vector_search_index_client():
    index_client = aiplatform_v1.IndexServiceClient(
        client_options=dict(api_endpoint=conf.value(Config.SECTION_PROJECT, "endpoint"))
    )
    return index_client
