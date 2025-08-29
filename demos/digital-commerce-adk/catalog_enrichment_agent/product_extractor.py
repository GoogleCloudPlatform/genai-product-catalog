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
import google.genai.types as types

INSTRUCTIONS = """Extract product data from the provided text, it may already be in JSON format,
at which time extract the JSON and ensure it's a valid JSON object, if not fix it to be valid.
If it is plain text, attempt to build a JSON object.

Example 1:

Input:
User: Fix this product: {"uniq_id":3125121,"crawl_timestamp":"2025-07-30 16:37:40 +0200","product_url":"https://base_url/prod3125121","product_name":"Stone Slim Fit T-shirt","product_category_tree":["Men >> Tops","Brands >> Men >> Fuel >> Tops","Men >> Tops >> T-shirts","Men >> Fuel","Men >> Fuel"],"pid":3125121,"retail_price":260,"discounted_price":null,"images":["https://image_url1.jpg","https://image_url2.jpg","https://image_url1.jpg"],"is_FK_Advantage_product":"FALSE","description":"Stone Slim Fit T-shirt by Fuel\r\n-Colour: Beige\r\n-Style: T-shirt\r\n-Fabric: Carded Single Jersey","product_rating":"No rating available","overall_rating":"No rating available","brand":"Fuel","product_specifications":[{"key":"Primary Colour","value":"Beige"},{"key":"Style","value":"T-shirts"},{"key":"Type","value":"T-Shirts"},{"key":"Age Group","value":"Adult"},{"key":"Gender","value":"Men"}]}
System: ```json {"uniq_id":3125121,"crawl_timestamp":"2025-07-30 16:37:40 +0200","product_url":"https://base_url/stone-slim-fit-t-shirt/product/prod3125121","product_name":"Stone Slim Fit T-shirt","product_category_tree":["Men >> Tops","Brands >> Men >> Fuel >> Tops","Men >> Tops >> T-shirts","Men >> Fuel","Men >> Fuel"],"pid":3125121,"retail_price":260,"discounted_price":null,"images":["https://image_url1.jpg","https://image_url2.jpg","https://image_url3.jpg"],"is_FK_Advantage_product":"FALSE","description":"Stone Slim Fit T-shirt by Fuel\r\n-Colour: Beige\r\n-Style: T-shirt\r\n-Fabric: Carded Single Jersey","product_rating":"No rating available","overall_rating":"No rating available","brand":"Fuel","product_specifications":[{"key":"Primary Colour","value":"Beige"},{"key":"Style","value":"T-shirts"},{"key":"Type","value":"T-Shirts"},{"key":"Age Group","value":"Adult"},{"key":"Gender","value":"Men"}]} ```

Example 2:
User: Fix the following product: SKU: abc-123, Name: Some Product, Description: some description, attributes: color: black, size: large
System: ```json {"sku":"abc-123","name":"Some Product","description":"some description","attributes":{"color":"black","size":"large"}}```

""

product_extractor_agent = LlmAgent(
    name="product_extractor_agent",
    description="An agent used for extracting JSON product data from the request",
    model="gemini-2.5-flash",
    instruction=INSTRUCTIONS,
    output_key="initial_product",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
    ),
)
