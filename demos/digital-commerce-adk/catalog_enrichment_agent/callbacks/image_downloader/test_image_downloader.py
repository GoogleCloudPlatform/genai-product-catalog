# Copyright 2026 Google, LLC.
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

"""Hermetic SSRF & artifact safety unit tests for ADK image_downloader."""

import asyncio
import importlib.util
import io
import json
import os
import pathlib
import socket
import sys
import types as pytypes
import unittest
from unittest import mock

_THIS_DIR = pathlib.Path(__file__).resolve().parent


def _load_image_downloader_module():
    """Load main.py with lightweight google.adk / google.genai stubs if absent."""
    stubbed = {}
    if "google.adk.agents.callback_context" not in sys.modules:
        google_pkg = sys.modules.setdefault("google", pytypes.ModuleType("google"))
        adk_pkg = pytypes.ModuleType("google.adk")
        agents_pkg = pytypes.ModuleType("google.adk.agents")
        ctx_mod = pytypes.ModuleType("google.adk.agents.callback_context")

        class CallbackContext:  # pragma: no cover - test stub
            pass

        ctx_mod.CallbackContext = CallbackContext
        google_pkg.adk = adk_pkg
        adk_pkg.agents = agents_pkg
        agents_pkg.callback_context = ctx_mod
        for name, mod in (
            ("google.adk", adk_pkg),
            ("google.adk.agents", agents_pkg),
            ("google.adk.agents.callback_context", ctx_mod),
        ):
            sys.modules[name] = mod
            stubbed[name] = mod

    if "google.genai.types" not in sys.modules:
        google_pkg = sys.modules.setdefault("google", pytypes.ModuleType("google"))
        genai_pkg = pytypes.ModuleType("google.genai")
        types_mod = pytypes.ModuleType("google.genai.types")

        class Part:
            def __init__(self, *, text=None, data=None, mime_type=None):
                self.text = text
                self.data = data
                self.mime_type = mime_type

            @classmethod
            def from_bytes(cls, *, data: bytes, mime_type: str):
                return cls(data=data, mime_type=mime_type)

        class Content:
            def __init__(self, *, parts=None, role=None):
                self.parts = parts or []
                self.role = role

        types_mod.Part = Part
        types_mod.Content = Content
        google_pkg.genai = genai_pkg
        genai_pkg.types = types_mod
        for name, mod in (
            ("google.genai", genai_pkg),
            ("google.genai.types", types_mod),
        ):
            sys.modules[name] = mod
            stubbed[name] = mod

    spec = importlib.util.spec_from_file_location(
        "adk_image_downloader_main", _THIS_DIR / "main.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


image_downloader = _load_image_downloader_module()

_MINIMAL_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


class _FakeHTTPResponse:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None):
        self._stream = io.BytesIO(payload)
        self.headers = headers or {}

    def read(self, n: int = -1) -> bytes:
        return self._stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeCallbackContext:
    def __init__(self, urls_state):
        self.agent_name = "image_loader_agent"
        self.state = {"product_images_urls": urls_state}
        self.saved_artifacts: list[tuple[str, object]] = []

    async def save_artifact(self, filename: str, part):
        self.saved_artifacts.append((filename, part))


class ImageDownloaderSSRFTest(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patcher.start()
        for key in (
            "ALLOWED_IMAGE_DOMAINS",
            "MAX_IMAGE_BYTES",
            "IMAGE_FETCH_TIMEOUT_SECONDS",
            "IMAGE_DOWNLOADER_MAX_URLS",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        self._env_patcher.stop()

    def test_rejects_disallowed_schemes_ports_credentials_and_hosts(self):
        blocked_urls = [
            "http://example.com/image.jpg",
            "file:///etc/passwd",
            "ftp://example.com/image.jpg",
            "gopher://127.0.0.1:70/",
            "https://user:pass@example.com/image.jpg",
            "https://example.com:8443/image.jpg",
            "https://localhost/admin",
            "https://foo.localhost/img.jpg",
            "https://metadata.google.internal/computeMetadata/v1/",
            "https://169.254.169.254/computeMetadata/v1/",
            "https://127.0.0.1/internal",
            "https://10.0.0.5/secret.png",
            "https://172.16.0.1/secret.png",
            "https://192.168.1.1/secret.png",
            "https://100.64.0.1/secret.png",
            "https://[::1]/secret.png",
            "https://[::ffff:127.0.0.1]/secret.png",
            "https://[::ffff:169.254.169.254]/latest/meta-data/",
            "https://[2002:7f00:0001::1]/secret.png",
            "https://[64:ff9b::169.254.169.254]/computeMetadata/v1/",
            "https://service.internal/img.jpg",
            "https://example.com/img.jpg\r\nX-Injected: 1",
        ]
        for url in blocked_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    image_downloader.validate_https_image_url(url)

    def test_rejects_public_hostname_resolving_to_private_or_metadata_ip(self):
        disallowed_ips = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.128.0.2", 443)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 443, 0, 0)),
        ]
        for addr_info in disallowed_ips:
            with self.subTest(addr=addr_info[4][0]):
                with mock.patch("socket.getaddrinfo", return_value=[addr_info]):
                    with self.assertRaises(ValueError):
                        image_downloader.validate_https_image_url(
                            "https://rebind.example.com/product.jpg"
                        )

    def test_enforces_optional_allowed_image_domains(self):
        os.environ["ALLOWED_IMAGE_DOMAINS"] = "cdn.media.amplience.net"
        public_addr = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        with mock.patch("socket.getaddrinfo", return_value=public_addr):
            validated_url, host, port, _ = image_downloader.validate_https_image_url(
                "https://cdn.media.amplience.net/i/truworths/prod_1.jpg"
            )
            self.assertEqual(host, "cdn.media.amplience.net")
            self.assertEqual(port, 443)
            self.assertTrue(validated_url.startswith("https://"))

            with self.assertRaises(ValueError):
                image_downloader.validate_https_image_url(
                    "https://evil-cdn.example.com/prod_1.jpg"
                )

    def test_blocks_redirects_and_http_errors_via_opener_pipeline(self):
        import email.message
        import urllib.error
        import urllib.request

        opener = image_downloader._build_safe_https_opener(
            "cdn.example.com",
            [(socket.AF_INET, socket.SOCK_STREAM, 6, ("93.184.216.34", 443))],
        )
        processor_types = [type(h) for h in opener.handlers]
        self.assertIn(urllib.request.HTTPErrorProcessor, processor_types)

        # Verify HTTPErrorProcessor routes 302 into _NoRedirectHandler (ValueError)
        # and 404/500 into HTTPDefaultErrorHandler (HTTPError)
        req = urllib.request.Request("https://cdn.example.com/pic.png")
        hdrs_302 = email.message.Message()
        hdrs_302["Location"] = "http://169.254.169.254/computeMetadata/v1/"
        resp_302 = mock.MagicMock()
        resp_302.code = 302
        resp_302.msg = "Found"
        resp_302.headers = hdrs_302
        resp_302.info.return_value = hdrs_302
        with self.assertRaises(ValueError):
            opener.process_response["https"][0].http_response(req, resp_302)

        hdrs_404 = email.message.Message()
        hdrs_404["Content-Type"] = "image/png"
        resp_404 = mock.MagicMock()
        resp_404.code = 404
        resp_404.msg = "Not Found"
        resp_404.headers = hdrs_404
        resp_404.info.return_value = hdrs_404
        with self.assertRaises(urllib.error.HTTPError):
            opener.process_response["https"][0].http_response(req, resp_404)

    def test_rejects_non_image_content_type_and_non_image_magic_bytes(self):
        public_addr = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]

        fake_json_resp = _FakeHTTPResponse(
            b'{"access_token": "secret"}',
            headers={"Content-Type": "application/json"},
        )
        fake_opener = mock.MagicMock()
        fake_opener.open.return_value = fake_json_resp

        with (
            mock.patch("socket.getaddrinfo", return_value=public_addr),
            mock.patch.object(
                image_downloader, "_build_safe_https_opener", return_value=fake_opener
            ),
        ):
            with self.assertRaises(ValueError):
                image_downloader.fetch_validated_image(
                    "https://cdn.example.com/not-an-image"
                )

        # Even if server lies with Content-Type: image/jpeg, reject non-image bytes
        fake_spoofed_resp = _FakeHTTPResponse(
            b"<html><body>internal admin panel</body></html>",
            headers={"Content-Type": "image/jpeg"},
        )
        fake_opener.open.return_value = fake_spoofed_resp
        with (
            mock.patch("socket.getaddrinfo", return_value=public_addr),
            mock.patch.object(
                image_downloader, "_build_safe_https_opener", return_value=fake_opener
            ),
        ):
            with self.assertRaises(ValueError):
                image_downloader.fetch_validated_image(
                    "https://cdn.example.com/spoof.jpg"
                )

    def test_rejects_oversized_response(self):
        public_addr = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        oversized = _MINIMAL_JPEG + b"A" * 2048
        fake_resp = _FakeHTTPResponse(
            oversized, headers={"Content-Type": "image/jpeg"}
        )
        fake_opener = mock.MagicMock()
        fake_opener.open.return_value = fake_resp

        with (
            mock.patch("socket.getaddrinfo", return_value=public_addr),
            mock.patch.object(
                image_downloader, "_build_safe_https_opener", return_value=fake_opener
            ),
        ):
            with self.assertRaises(ValueError):
                image_downloader.fetch_validated_image(
                    "https://cdn.example.com/huge.jpg", max_bytes=128
                )

    def test_callback_blocks_ssrf_and_saves_only_valid_public_images_safely(self):
        public_addr = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        urls = [
            "http://169.254.169.254/computeMetadata/v1/",
            "https://127.0.0.1/secret",
            "https://cdn.example.com/..%2f..%2fprod_123?fmt=png",
        ]
        ctx = _FakeCallbackContext(json.dumps(urls))

        fake_resp = _FakeHTTPResponse(
            _MINIMAL_PNG, headers={"Content-Type": "image/png"}
        )
        fake_opener = mock.MagicMock()
        fake_opener.open.return_value = fake_resp

        with (
            mock.patch("socket.getaddrinfo", return_value=public_addr),
            mock.patch.object(
                image_downloader, "_build_safe_https_opener", return_value=fake_opener
            ),
        ):
            result = asyncio.run(
                image_downloader.download_and_add_images_to_artifacts(ctx)
            )

        self.assertIn("1/3", result.parts[0].text)
        self.assertEqual(len(ctx.saved_artifacts), 1)
        saved_name, saved_part = ctx.saved_artifacts[0]
        self.assertEqual(saved_name, "downloaded_image_prod_123")
        self.assertNotIn("..", saved_name)
        self.assertNotIn("/", saved_name)
        self.assertNotIn("?", saved_name)
        self.assertEqual(saved_part.mime_type, "image/png")
        self.assertEqual(saved_part.data, _MINIMAL_PNG)


if __name__ == "__main__":
    unittest.main()
