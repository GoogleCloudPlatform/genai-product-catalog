# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Hermetic unit tests for SSRF, LFI, and GCS allowlist protections in image_to_text."""

import io
import os
import pathlib
import socket
import sys
import unittest
from unittest import mock

_EXPERIMENTS_DIR = pathlib.Path(__file__).resolve().parents[5]
_SERVICE_DIR = _EXPERIMENTS_DIR / "examples" / "service"
for _p in (str(_EXPERIMENTS_DIR), str(_SERVICE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("APPLIED_AI_CONF", str(_EXPERIMENTS_DIR / "conf" / "app.toml"))

with mock.patch("vertexai.preview.generative_models.GenerativeModel", autospec=True):
    from google.cloud.ml.applied.images import image_to_text
    from google.cloud.ml.applied.model import domain_model as m


class _FakeHTTPResponse:
    def __init__(self, body: bytes, headers: dict[str, str] | None = None):
        self._stream = io.BytesIO(body)
        self.headers = headers or {}

    def read(self, amt: int | None = None) -> bytes:
        return self._stream.read(amt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ImageToTextSecurityTest(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patcher.start()
        for key in (
            "ALLOWED_IMAGE_GCS_BUCKETS",
            "ALLOWED_GCS_BUCKETS",
            "ALLOWED_IMAGE_GCS_PREFIXES",
            "MAX_IMAGE_BYTES",
            "IMAGE_FETCH_TIMEOUT_SECONDS",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        self._env_patcher.stop()

    def test_rejects_non_https_schemes_including_file_and_http(self):
        disallowed_urls = [
            "file:///etc/passwd",
            "file:///tmp/fake_adc.json",
            "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
            "http://example.com/product.jpg",
            "ftp://example.com/product.jpg",
            "data:image/png;base64,iVBORw0KGgo=",
            "gopher://127.0.0.1:70/_test",
            "/etc/passwd",
            "",
        ]
        for bad_url in disallowed_urls:
            with self.subTest(url=bad_url):
                with self.assertRaises(ValueError):
                    image_to_text.get_image_bytes_from_url(bad_url)

    def test_rejects_forbidden_hosts_and_ip_literals(self):
        forbidden_https_urls = [
            "https://localhost/image.jpg",
            "https://sub.localhost/image.jpg",
            "https://metadata.google.internal/computeMetadata/v1/",
            "https://metadata.google.internal./computeMetadata/v1/",
            "https://service.internal/image.jpg",
            "https://127.0.0.1/image.jpg",
            "https://169.254.169.254/latest/meta-data/",
            "https://10.0.0.5/image.jpg",
            "https://172.16.0.10/image.jpg",
            "https://192.168.1.20/image.jpg",
            "https://100.64.0.1/image.jpg",
            "https://0.0.0.0/image.jpg",
            "https://[::1]/image.jpg",
            "https://[::ffff:169.254.169.254]/image.jpg",
            "https://[::ffff:127.0.0.1]/image.jpg",
            "https://[fe80::1]/image.jpg",
            "https://user:pass@example.com/image.jpg",
        ]
        for bad_url in forbidden_https_urls:
            with self.subTest(url=bad_url):
                with self.assertRaises(ValueError):
                    image_to_text.get_image_bytes_from_url(bad_url)

    def test_rejects_hostname_resolving_to_internal_or_metadata_ips(self):
        bad_ips = [
            (socket.AF_INET, "169.254.169.254"),
            (socket.AF_INET, "127.0.0.1"),
            (socket.AF_INET, "10.128.0.2"),
            (socket.AF_INET, "172.31.255.1"),
            (socket.AF_INET, "192.168.0.1"),
            (socket.AF_INET, "100.64.10.10"),
            (socket.AF_INET, "224.0.0.1"),
            (socket.AF_INET, "0.0.0.0"),
            (socket.AF_INET6, "::1"),
            (socket.AF_INET6, "fe80::1234"),
            (socket.AF_INET6, "::ffff:169.254.169.254"),
        ]
        for family, ip_addr in bad_ips:
            sockaddr = (ip_addr, 443) if family == socket.AF_INET else (ip_addr, 443, 0, 0)
            fake_addrinfo = [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]
            with self.subTest(resolved_ip=ip_addr):
                with mock.patch("socket.getaddrinfo", return_value=fake_addrinfo):
                    with self.assertRaises(ValueError):
                        image_to_text.get_image_bytes_from_url("https://attacker.example.com/p.jpg")

    def test_blocks_http_redirects_to_metadata_or_file(self):
        redirect_handler = image_to_text._NoRedirectHandler()
        req = image_to_text.urllib.request.Request("https://cdn.example.com/img.jpg")
        for status_code, target in [
            (301, "http://169.254.169.254/computeMetadata/v1/"),
            (302, "file:///etc/passwd"),
            (307, "https://127.0.0.1/internal"),
            (308, "https://cdn.example.com/other.jpg"),
        ]:
            with self.subTest(code=status_code, target=target):
                with self.assertRaises(ValueError):
                    redirect_handler.redirect_request(
                        req, None, status_code, "Redirect", {}, target
                    )

    def test_enforces_max_image_size_and_non_empty_body(self):
        public_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        ]
        with mock.patch("socket.getaddrinfo", return_value=public_addrinfo):
            # Declared Content-Length over max_bytes
            oversized_header_resp = _FakeHTTPResponse(
                b"abc", headers={"Content-Length": "2048"}
            )
            with mock.patch.object(
                image_to_text.urllib.request.OpenerDirector,
                "open",
                return_value=oversized_header_resp,
            ):
                with self.assertRaises(ValueError):
                    image_to_text.get_image_bytes_from_url(
                        "https://cdn.example.com/img.jpg", max_bytes=1024
                    )

            # Streaming body over max_bytes without Content-Length
            oversized_body_resp = _FakeHTTPResponse(b"x" * 1025)
            with mock.patch.object(
                image_to_text.urllib.request.OpenerDirector,
                "open",
                return_value=oversized_body_resp,
            ):
                with self.assertRaises(ValueError):
                    image_to_text.get_image_bytes_from_url(
                        "https://cdn.example.com/img.jpg", max_bytes=1024
                    )

            # Empty body rejected
            empty_resp = _FakeHTTPResponse(b"")
            with mock.patch.object(
                image_to_text.urllib.request.OpenerDirector,
                "open",
                return_value=empty_resp,
            ):
                with self.assertRaises(ValueError):
                    image_to_text.get_image_bytes_from_url("https://cdn.example.com/img.jpg")

    def test_allows_valid_public_https_image_fetch(self):
        public_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        ]
        expected_bytes = b"\x89PNG\r\n\x1a\nvalid-image-payload"
        with mock.patch("socket.getaddrinfo", return_value=public_addrinfo):
            with mock.patch.object(
                image_to_text.urllib.request.OpenerDirector,
                "open",
                return_value=_FakeHTTPResponse(
                    expected_bytes, headers={"Content-Length": str(len(expected_bytes))}
                ),
            ) as mock_open:
                result = image_to_text.get_image_bytes_from_url(
                    "https://cdn.example.com/catalog/item.png"
                )
                self.assertEqual(result, expected_bytes)
                mock_open.assert_called_once()

    def test_pinned_connection_rejects_dns_rebinding_peer_ip(self):
        validated_addrs = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, ("93.184.216.34", 443))
        ]
        conn = image_to_text._PinnedHTTPSConnection(
            "cdn.example.com",
            expected_host="cdn.example.com",
            validated_addrs=validated_addrs,
            timeout=5.0,
        )
        fake_sock = mock.MagicMock()
        fake_sock.getpeername.return_value = ("169.254.169.254", 443)
        with mock.patch("socket.socket", return_value=fake_sock):
            with self.assertRaises(ValueError):
                conn.connect()
        fake_sock.close.assert_called_once()

    def test_gcs_uri_fails_closed_when_allowlist_unconfigured(self):
        with self.assertRaises(ValueError):
            image_to_text.from_gsc_uri("gs://any-bucket/product.jpg")

    def test_gcs_uri_validates_bucket_allowlist_traversal_and_prefix(self):
        os.environ["ALLOWED_IMAGE_GCS_BUCKETS"] = "trusted-catalog-bucket"
        os.environ["ALLOWED_IMAGE_GCS_PREFIXES"] = "products/images"

        # Disallowed bucket
        with self.assertRaises(ValueError):
            image_to_text.from_gsc_uri("gs://other-secret-bucket/products/images/item.jpg")

        # Path traversal variants
        for bad_uri in [
            "gs://trusted-catalog-bucket/products/images/../../secret.json",
            "gs://trusted-catalog-bucket/products/images/%2e%2e/secret.json",
            "gs://trusted-catalog-bucket//products/images/item.jpg",
            "gs://trusted-catalog-bucket/products/images/item.jpg?generation=1",
            "gs://trusted-catalog-bucket",
            "gs://trusted-catalog-bucket/",
        ]:
            with self.subTest(uri=bad_uri):
                with self.assertRaises(ValueError):
                    image_to_text.from_gsc_uri(bad_uri)

        # Prefix boundary check (must not match products/images-other)
        with self.assertRaises(ValueError):
            image_to_text.from_gsc_uri(
                "gs://trusted-catalog-bucket/products/images-other/item.jpg"
            )

        # Allowed bucket + allowed prefix succeeds
        sentinel_part = object()
        with mock.patch.object(
            image_to_text.Part, "from_uri", return_value=sentinel_part
        ) as mock_from_uri:
            part = image_to_text.from_gsc_uri(
                "gs://trusted-catalog-bucket/products/images/shoe.jpg"
            )
            self.assertIs(part, sentinel_part)
            mock_from_uri.assert_called_once_with(
                "gs://trusted-catalog-bucket/products/images/shoe.jpg",
                mime_type="image/jpeg",
            )

    def test_images_router_returns_400_on_ssrf_lfi_and_generic_500_on_unexpected_error(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from routers.images import router as image_router

        test_app = FastAPI()
        test_app.include_router(image_router, prefix="/images")
        client = TestClient(test_app)

        # PoC payload: file:///etc/passwd -> HTTP 400
        resp = client.post(
            "/images/api/v1/genai/images/descriptions",
            json={"image": "file:///etc/passwd"},
        )
        self.assertEqual(resp.status_code, 400)

        # Metadata SSRF payload -> HTTP 400
        resp_meta = client.post(
            "/images/api/v1/genai/images/attributes",
            json={"image": "http://169.254.169.254/computeMetadata/v1/"},
        )
        self.assertEqual(resp_meta.status_code, 400)

        # Unallowlisted GCS URI -> HTTP 400
        resp_gcs = client.post(
            "/images/api/v1/genai/images/descriptions",
            json={"image": "gs://untrusted-bucket/object.jpg"},
        )
        self.assertEqual(resp_gcs.status_code, 400)

        # Internal exception -> generic HTTP 500 without leaking sensitive exception message
        with mock.patch.object(
            image_to_text,
            "image_to_product_description",
            side_effect=RuntimeError("sensitive-internal-credentials-path"),
        ):
            resp_err = client.post(
                "/images/api/v1/genai/images/descriptions",
                json={"image": "https://cdn.example.com/item.jpg"},
            )
            self.assertEqual(resp_err.status_code, 500)
            self.assertEqual(resp_err.json(), {"detail": "Internal server error"})
            self.assertNotIn("sensitive-internal-credentials-path", resp_err.text)


if __name__ == "__main__":
    unittest.main()
