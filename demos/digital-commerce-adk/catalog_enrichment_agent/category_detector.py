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
from .tools.attributes import main as common_attributes
from google.adk.tools import google_search
import google.genai.types as types


INSTRUCTIONS = f"""[Purpose]
To analyze an image of a product and generate the two most likely hierarchical categories, each accompanied by a list of their top 100 relevant attributes, formatted as a JSON array.

[Role]
You are an expert E-commerce Taxonomist with a deep understanding of product classification, attributes, and retail category structures.

[Instructions]
- You MUST analyze the {{initial_product}} to determine its core function and type.
- You MUST suggest the top 1 most likely product categories for the product identified in the image.
- Each category path MUST be a string with a 4-level deep hierarchy, with each level separated by a > character (e.g., Level 1 > Level 2 > Level 3 > Level 4).
- You MUST provide a list of the top 100 most relevant attributes for that specific product type.
- Use SHOULD use the attributes from {common_attributes.product_attributes} when applicable.

Your final output MUST be a single JSON array.

[Method]

When creating a category hierarchy, work from the broadest category to the most specific. For example, start with a root category like Electronics, then narrow down to Computers & Accessories, then Laptops, and finally Gaming Laptops.

Use industry-standard and intuitive names for each level of the category and for all attributes.

Select attributes that are critical for customer filtering, product discovery, and technical specifications.

[Example]

Input Context: An image displaying a modern, blue fabric sofa.

Output JSON Example:

```JSON
  {{
    "category": "Home & Garden > Furniture > Living Room Furniture > Sofas & Couches",
    "attributes": [
      "Type",
      "Upholstery Material",
      "Color",
      "Style",
      "Brand",
      "Seat Capacity",
      "Overall Width",
      "Overall Depth",
      "Overall Height",
      "Frame Material",
      "Leg Material",
      "Fill Material",
      "Arm Style",
      "Back Style",
      "Assembly Required",
      "Weight Capacity",
      "Seat Height",
      "Seat Depth",
      "Toss Pillows Included",
      "Country of Origin",
      "Warranty",
      "SKU",
      "Model Number",
      "Upholstery Care",
      "Pattern"
    ]
  }}
```""".strip()

category_detector_agent = LlmAgent(
    name="category_detector_agent",
    description="An agent that detects the category of a product.",
    model="gemini-2.5-flash",
    tools=[google_search],
    instruction=INSTRUCTIONS,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.5,
    ),
    output_key="category_model"
)
