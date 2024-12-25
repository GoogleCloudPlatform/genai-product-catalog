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

import os
import tomllib

DATA: dict = None
configuration_file = os.environ.get("APPLIED_AI_CONF", "../../conf/app.toml")
with open(configuration_file, "rb") as f:
    DATA = tomllib.load(f)


class Config:
    DEFAULT_CONFIG = "conf/app.ini"
    SECTION_DEFAULT = "default"
    SECTION_PROJECT = "project"
    SECTION_GCS = "gcs"
    SECTION_MODELS = "models"
    SECTION_VECTORS = "vectors"
    SECTION_BIG_QUERY = "big_query"
    SECTION_CATEGORY = "category"
    SECTION_TEST = "test"

    @staticmethod
    def value(
        section: str = SECTION_DEFAULT, key: str = None
    ) -> str | list[any] | int | float | bool | None:
        if key is not None:
            return DATA[section][key]
        return None
