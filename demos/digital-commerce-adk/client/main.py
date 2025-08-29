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
import json
import os
import subprocess
import threading
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv


class ADKClient:
    """A client for interacting with an ADK agent deployed on Cloud Run."""

    _lock = threading.Lock()
    _token: Optional[str] = None

    def __init__(self):
        """Initializes the client, loading configuration from a .env file."""
        load_dotenv()
        self.app_url = os.getenv("APP_URL")
        self.app_name = os.getenv("APP_NAME", "catalog_enrichment_agent")
        self._token_env = os.getenv("ADK_TOKEN")

        if not self.app_url:
            raise ValueError("APP_URL not found in .env file or environment variables.")

        self.session = requests.Session()

    def _get_identity_token(self) -> str:
        """
        Gets the identity token from the environment or gcloud.
        Caches the token for subsequent requests.
        """
        with self._lock:
            if self._token:
                return self._token

            if self._token_env:
                self._token = self._token_env
                return self._token

            try:
                self._token = (
                    subprocess.check_output(["gcloud", "auth", "print-identity-token"])
                    .decode("utf-8")
                    .strip()
                )
                return self._token
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise RuntimeError(
                    "Could not get identity token. Please run 'gcloud auth login' "
                    "or set the ADK_TOKEN environment variable."
                ) from e

    def _get_headers(self) -> Dict[str, str]:
        """Returns the authorization headers for API requests."""
        token = self._get_identity_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def update_session(self, user_id: str, session_id: str, state: Dict[str, Any]):
        """
        Initializes or updates a session for a user.

        Args:
            user_id: The ID of the user.
            session_id: The ID of the session.
            state: A dictionary representing the session state.
        """
        url = f"{self.app_url}/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        response = self.session.post(url, headers=self._get_headers(), json={"state": state})
        response.raise_for_status()

    def enrich_product(
        self,
        product_data: Dict[str, Any],
        user_id: str = "user_123",
        session_id: str = "session_abc",
    ) -> Dict[str, Any]:
        """
        Runs the agent with the given product data.

        Args:
            product_data: A dictionary containing the product data.
            user_id: The user ID for the session.
            session_id: The session ID for the session.

        Returns:
            A dictionary containing the agent's response.
        """
        data = {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": json.dumps(product_data)}],
            },
            "streaming": False,
        }
        response = self.session.post(
            f"{self.app_url}/run_sse", headers=self._get_headers(), json=data
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # This is an example of how to use the ADKClient library.
    # Make sure you have a .env file in the root of the project with
    # APP_URL and optionally APP_NAME and ADK_TOKEN defined.
    # You also need a test_data.json file in the resources directory.

    client = ADKClient()

    # Example: Update session state
    client.update_session(
        user_id="user_123",
        session_id="session_abc",
        state={"preferred_language": "English"},
    )
    print("Session updated.")

    # Example: Enrich a product
    with open("../resources/test_data.json", "r") as f:
        test_product_data = json.load(f)

    result = client.enrich_product(test_product_data)
    print(json.dumps(result, indent=2))
