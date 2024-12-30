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

from typing import Dict, Optional

import logging
import tomllib

import vertexai.generative_models
import vertexai.language_models
from common import utils

from common.utils import get_env_file_name

from sqlmodel import create_engine

import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Tool,
    grounding,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)

logger = logging.getLogger(__name__)

class TomlClass:
    def __init__(self, d: Dict[str, any] = None):
        if d is not None:
            for k, v in d.items():
                logger.debug("creating value for property: %s", k)
                setattr(self, k, v)

    def updateValues(self, d: Dict[str, any] = None):
        if d is not None:
            for k, v in d.items():
                logger.debug("overriding value for property: %s", k)
                setattr(self, k, v)

class Application(TomlClass):
    project_id: Optional[str] = None
    api_key: Optional[str] = None
    location: Optional[str] = "us-central1"
    thread_pool_size: Optional[int] = 20

class Embedding(TomlClass):
    text_embedding_model: Optional[str] = "text-embedding-004"
    multimodal_embedding_model: Optional[str] = "multimodalembedding"
    max_requests_per_minute: Optional[int] = 900

class Gemini(TomlClass):
    model: GenerativeModel
    config: GenerationConfig
    model_name: Optional[str] = "gemini-1.5-flash-002"
    temperature: Optional[float] = 0.8
    top_p: Optional[float] = 0.6
    top_k: Optional[int] = 40
    max_output_tokens: Optional[int] = 8192
    output_format: Optional[str] = "application/json"

    def get_generative_config(self) -> GenerationConfig:
        return GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens,
            response_mime_type=self.output_format)

    def get_model(self, instruction: str) -> GenerativeModel:
        tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

        safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

        return vertexai.generative_models.GenerativeModel(
            model_name=self.model_name,
            system_instruction=instruction,
            generation_config=self.get_generative_config(),
            tools=[tool],
            safety_settings=safety_settings
        )

class GenAI(TomlClass):
    embedding: Embedding
    gemini_creative: Gemini
    gemini_grounded: Gemini
    gemini_critic: Gemini

class Postgres(TomlClass):
    salt: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = "gcp-genai-catalog"
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 8000

    def __get_url(self):
        if (self.salt is not None) and (self.database is not None) and (self.user is not None) and (self.password is not None):
            return "postgresql+psycopg://{}:{}@{}:{}/{}".format(self.user, utils.decrypt(self.password,self.salt), self.host, self.port, self.database)
        else:
            return "Invalid URL"

    def get_engine(self, echo: bool):
        return create_engine(self.__get_url(), echo=echo)

class Config:
    application: Application
    generative_ai: GenAI
    postgres: Postgres

    def __init__(self, file_name):
        env_file_name = get_env_file_name(file_name)
        with open(file_name, "rb") as f:
            print("Loading configuration from file: ", file_name)
            data = tomllib.load(f)
            setattr(self, "application", Application(data.get("application")))
            setattr(self, "postgres", Postgres(data.get("postgres")))
            v = GenAI()
            v.embedding = Embedding(data.get("generative_ai")["embedding"])
            v.gemini_creative = Gemini(data.get("generative_ai")["gemini_creative"])
            v.gemini_grounded = Gemini(data.get("generative_ai")["gemini_grounded"])
            v.gemini_critic = Gemini(data.get("generative_ai")["gemini_critic"])
            setattr(self, "generative_ai", v)

        if env_file_name is not None:
            with open(env_file_name, "rb") as f:
                print("Loading environment config file: ", env_file_name)
                data = tomllib.load(f)
                self.application.updateValues(data.get("application"))
                self.postgres.updateValues(data.get("postgres"))
                if data.get("generative_ai") is not None:
                    self.generative_ai.embedding.updateValues(data.get("generative_ai")["embedding"])
                    self.generative_ai.gemini_creative.updateValues(data.get("generative_ai")["gemini_creative"])
                    self.generative_ai.gemini_grounded.updateValues(data.get("generative_ai")["gemini_grounded"])
                    self.generative_ai.gemini_critic.updateValues(data.get("generative_ai")["gemini_critic"])
