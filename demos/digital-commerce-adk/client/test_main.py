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
from unittest.mock import patch, MagicMock

import pytest
from client.main import ADKClient


@pytest.fixture
def mock_env():
    """Mocks environment variables for the client."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: {
            "APP_URL": "http://fake-test-url.com",
            "APP_NAME": "test_agent",
            "ADK_TOKEN": "test_token",
        }.get(key, default)
        yield


def test_adk_client_enrich_product(mock_env):
    """Tests the enrich_product method of the ADKClient."""
    client = ADKClient()
    product_data = {"name": "Test Product"}
    expected_response = {"parts": [{"text": '{"enriched": true}'}]}

    # Mock the session object and its post method
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = expected_response
    mock_session.post.return_value = mock_response
    client.session = mock_session

    result = client.enrich_product(product_data, user_id="user1", session_id="session1")

    # Verify the correct URL and data were sent
    expected_url = "http://fake-test-url.com/run_sse"
    expected_payload = {
        "app_name": "test_agent",
        "user_id": "user1",
        "session_id": "session1",
        "new_message": {
            "role": "user",
            "parts": [{"text": json.dumps(product_data)}],
        },
        "streaming": False,
    }
    mock_session.post.assert_called_once_with(
        expected_url, headers=client._get_headers(), json=expected_payload
    )

    # Verify the result
    assert result == expected_response


def test_adk_client_update_session(mock_env):
    """Tests the update_session method of the ADKClient."""
    client = ADKClient()
    state_data = {"key": "value"}

    # Mock the session object and its post method
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response
    client.session = mock_session

    client.update_session(user_id="user1", session_id="session1", state=state_data)

    # Verify the correct URL and data were sent
    expected_url = "http://fake-test-url.com/apps/test_agent/users/user1/sessions/session1"
    expected_payload = {"state": state_data}
    mock_session.post.assert_called_once_with(
        expected_url, headers=client._get_headers(), json=expected_payload
    )
