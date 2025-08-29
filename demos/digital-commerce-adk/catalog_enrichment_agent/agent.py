# Copyright 2024 Google, LLC.
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
from google.adk.agents import SequentialAgent
from .attribute_mapper import attribute_mapper_agent
from .category_detector import category_detector_agent
from .judge import judge_agent
from .product_extractor import product_extractor_agent
from .image_loader import image_loader_agent

root_agent = SequentialAgent(
    name="catalog_item_enrichment_agent",
    description="A workflow agent for catalog enrichment",
    sub_agents=[product_extractor_agent, image_loader_agent, category_detector_agent, attribute_mapper_agent, judge_agent],
)
