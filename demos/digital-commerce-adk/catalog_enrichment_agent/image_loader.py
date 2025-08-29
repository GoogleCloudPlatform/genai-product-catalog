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
from google.adk.agents import LlmAgent
from .callbacks.image_downloader.main import download_and_add_images_to_artifacts
import google.genai.types as types

INSTRUCTIONS = """
Extract all image URLs into a single list of URLs

Example Output:
["https://cdn.media.amplience.net/i/truworths/prod3125121_1?fmt=jpg",
"https://cdn.media.amplience.net/i/truworths/prod3125121_2?fmt=jpg" ]
"""

image_loader_agent = LlmAgent(
    name="image_loader_agent",
    description="An agent used for extracting image URLs into a list of URLs",
    model="gemini-2.5-flash",
    instruction=INSTRUCTIONS,
    output_key="product_images_urls",
    after_agent_callback=download_and_add_images_to_artifacts,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
    ),
)
