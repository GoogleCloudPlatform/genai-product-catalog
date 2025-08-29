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
import concurrent.futures
import io
from typing import Any, Dict
from typing import Optional
import json
import requests
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

async def download_and_add_images_to_artifacts(callback_context: CallbackContext) ->  Optional[types.Content]:
    """
    Downloads images from a list of URLs in parallel and adds them to the context artifacts.

    This tool retrieves a list of image URLs from the 'product_images' key in the context.
    It then downloads these images concurrently and adds them as artifacts to the context.

    Args:
        callback_context: The tool context from the Gemini ADK agent.
                 It is expected to contain a key 'product_images' with a list of image URLs.

    Returns:
        A string indicating the result of the operation.
    """
    product_images = callback_context.state.get("product_images_urls")
    print(callback_context.agent_name)
    print(product_images)
    if not product_images:
        return types.Content(
            parts=[types.Part(text=f"skipped due to state.")],
            role="model" # Assign model role to the overriding response
        )
    else:
        product_images = product_images.replace("```json\n", "").replace("\n```", "")
        product_images = json.loads(product_images)

    def download_image(url: str) -> Dict[str, Any]:
        """Downloads a single image and returns it as a dictionary with URL and content."""
        print(url)
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            return {"url": url, "content": response.content, "error": None}
        except requests.exceptions.RequestException as e:
            return {"url": url, "content": None, "error": str(e)}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Download images in parallel
        future_to_url = {executor.submit(download_image, url): url for url in product_images}
        downloaded_images = [future.result() for future in concurrent.futures.as_completed(future_to_url)]

    successful_downloads = 0
    for result in downloaded_images:
        if result["content"]:
            # Create an in-memory artifact for the downloaded image
            file_name = f"downloaded_image_{result['url'].split('/')[-1]}"
            content = io.BytesIO(result["content"])
            image_part = types.Part.from_bytes(data=content.getvalue(), mime_type="image/jpeg")

            await callback_context.save_artifact(file_name, image_part)
            successful_downloads += 1
        else:
            print(f"Failed to download {result['url']}: {result['error']}")

    return types.Content(parts=[types.Part(text=f"Successfully downloaded and added {successful_downloads}/{len(product_images)} images to artifacts.")], role="model")
