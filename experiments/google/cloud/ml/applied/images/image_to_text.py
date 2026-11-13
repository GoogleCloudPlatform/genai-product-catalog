#  Copyright 2023 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import http.client
import ipaddress
import json
import logging
import os
import re
import socket
import ssl
import typing
import urllib.error
import urllib.parse
import urllib.request

from google.cloud.ml.applied.model import domain_model as m
from google.cloud.ml.applied.utils import utils
from vertexai.preview.generative_models import Image, Part

multimodal_model = utils.get_gemini_pro_vision()

DEFAULT_FETCH_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MiB

_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
_LINK_LOCAL_V4_NETWORK = ipaddress.ip_network("169.254.0.0/16")
_FORBIDDEN_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata",
        "metadata.google.internal",
    }
)
_GCS_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]$")


def _get_fetch_timeout() -> float:
    raw = os.environ.get("IMAGE_FETCH_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_FETCH_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ValueError("Invalid IMAGE_FETCH_TIMEOUT_SECONDS configuration") from exc
    if timeout <= 0 or timeout > 60:
        raise ValueError("IMAGE_FETCH_TIMEOUT_SECONDS must be between 0 and 60")
    return timeout


def _get_max_image_bytes() -> int:
    raw = os.environ.get("MAX_IMAGE_BYTES", "").strip()
    if not raw:
        return DEFAULT_MAX_IMAGE_BYTES
    try:
        max_bytes = int(raw)
    except ValueError as exc:
        raise ValueError("Invalid MAX_IMAGE_BYTES configuration") from exc
    if max_bytes <= 0 or max_bytes > 50 * 1024 * 1024:
        raise ValueError("MAX_IMAGE_BYTES must be between 1 and 52428800")
    return max_bytes


def _check_single_ip(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> None:
    if (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        or not addr.is_global
    ):
        raise ValueError("Image URL resolves to a disallowed non-public IP address")
    if isinstance(addr, ipaddress.IPv4Address) and (
        addr in _CGNAT_NETWORK or addr in _LINK_LOCAL_V4_NETWORK
    ):
        raise ValueError("Image URL resolves to a disallowed reserved IP address")


def _validate_ip_address(
    ip_str: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if "%" in ip_str:
        raise ValueError("IPv6 zone identifiers are not allowed in image URLs")
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError as exc:
        raise ValueError("Invalid IP address for image URL") from exc

    _check_single_ip(addr)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        _check_single_ip(addr.ipv4_mapped)
    return addr


def _validate_hostname(hostname: str) -> str:
    normalized = hostname.rstrip(".").lower()
    if not normalized:
        raise ValueError("Image URL must include a valid hostname")
    if (
        normalized in _FORBIDDEN_HOSTNAMES
        or normalized.endswith(".localhost")
        or normalized.endswith(".internal")
        or normalized.endswith(".local")
    ):
        raise ValueError("Image URL hostname is not allowed")

    # If hostname is an IP literal, validate it directly before DNS lookup.
    try:
        ipaddress.ip_address(normalized.split("%")[0])
        is_ip_literal = True
    except ValueError:
        is_ip_literal = False

    if is_ip_literal:
        _validate_ip_address(normalized)

    return normalized


def _resolve_and_validate_host(
    hostname: str, port: int
) -> list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]]:
    normalized_host = _validate_hostname(hostname)
    try:
        addr_infos = socket.getaddrinfo(
            normalized_host, port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve image URL hostname") from exc

    if not addr_infos:
        raise ValueError("Image URL hostname did not resolve to any address")

    validated: list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]] = []
    for family, socktype, proto, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        _validate_ip_address(ip_str)
        validated.append((family, socktype, proto, sockaddr))
    return validated


def validate_https_image_url(
    image_url: str,
) -> tuple[str, str, int, list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]]]:
    if not isinstance(image_url, str) or not image_url.strip():
        raise ValueError("Image URL must be a non-empty string")
    if any(ch in image_url for ch in ("\r", "\n", "\x00", " ", "\t")):
        raise ValueError("Image URL contains invalid control or whitespace characters")

    parsed = urllib.parse.urlsplit(image_url)
    if parsed.scheme.lower() != "https":
        raise ValueError("Invalid image URL scheme: only https:// is allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in image URLs are not allowed")
    if not parsed.hostname:
        raise ValueError("Image URL must specify a hostname")

    try:
        port = parsed.port if parsed.port is not None else 443
    except ValueError as exc:
        raise ValueError("Invalid port in image URL") from exc
    if port < 1 or port > 65535:
        raise ValueError("Invalid port in image URL")

    validated_addrs = _resolve_and_validate_host(parsed.hostname, port)
    return image_url, parsed.hostname, port, validated_addrs


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError(f"HTTP redirects are not allowed for image URLs (HTTP {code})")


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        *,
        expected_host: str,
        validated_addrs: list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]],
        port: int | None = None,
        timeout: float = DEFAULT_FETCH_TIMEOUT_SECONDS,
        context: ssl.SSLContext | None = None,
        **kwargs,
    ):
        super().__init__(host, port=port, timeout=timeout, context=context, **kwargs)
        self._expected_host = expected_host.rstrip(".").lower()
        self._validated_addrs = validated_addrs
        self._ssl_context = context or ssl.create_default_context()

    def connect(self) -> None:
        if self.host.rstrip(".").lower() != self._expected_host:
            raise ValueError("Unexpected target host during HTTPS connection")

        last_err: OSError | None = None
        raw_sock: socket.socket | None = None
        for family, socktype, proto, sockaddr in self._validated_addrs:
            candidate: socket.socket | None = None
            try:
                candidate = socket.socket(family, socktype, proto)
                candidate.settimeout(self.timeout)
                candidate.connect(sockaddr)
                peer_ip = candidate.getpeername()[0]
                _validate_ip_address(peer_ip)
                raw_sock = candidate
                break
            except ValueError:
                if candidate is not None:
                    candidate.close()
                raise
            except OSError as err:
                last_err = err
                if candidate is not None:
                    candidate.close()

        if raw_sock is None:
            raise OSError(
                f"Failed to connect to validated address for {self.host}"
            ) from last_err

        try:
            self.sock = self._ssl_context.wrap_socket(
                raw_sock, server_hostname=self.host
            )
        except Exception:
            raw_sock.close()
            raise


class _PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(
        self,
        expected_host: str,
        validated_addrs: list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]],
        context: ssl.SSLContext | None = None,
    ):
        super().__init__(context=context)
        self._expected_host = expected_host
        self._validated_addrs = validated_addrs
        self._ssl_context = context or ssl.create_default_context()

    def https_open(self, req: urllib.request.Request):
        def _connection_factory(host: str, **kwargs):
            return _PinnedHTTPSConnection(
                host,
                expected_host=self._expected_host,
                validated_addrs=self._validated_addrs,
                context=self._ssl_context,
                **kwargs,
            )

        return self.do_open(_connection_factory, req)


def _build_safe_https_opener(
    expected_host: str,
    validated_addrs: list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]],
) -> urllib.request.OpenerDirector:
    opener = urllib.request.OpenerDirector()
    opener.add_handler(_PinnedHTTPSHandler(expected_host, validated_addrs))
    opener.add_handler(_NoRedirectHandler())
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    return opener


def get_image_bytes_from_url(
    image_url: str,
    *,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> bytes:
    validated_url, hostname, _, validated_addrs = validate_https_image_url(image_url)
    effective_timeout = _get_fetch_timeout() if timeout is None else timeout
    effective_max_bytes = _get_max_image_bytes() if max_bytes is None else max_bytes

    opener = _build_safe_https_opener(hostname, validated_addrs)
    req = urllib.request.Request(
        validated_url,
        method="GET",
        headers={"User-Agent": "genai-product-catalog-image-fetcher/1.0"},
    )
    try:
        with opener.open(req, timeout=effective_timeout) as response:
            response = typing.cast(http.client.HTTPResponse, response)
            content_length = response.headers.get("Content-Length") if response.headers else None
            if content_length is not None:
                try:
                    declared_len = int(content_length)
                except ValueError as exc:
                    raise ValueError("Invalid Content-Length header in image response") from exc
                if declared_len < 0 or declared_len > effective_max_bytes:
                    raise ValueError("Image response exceeds maximum allowed byte size")

            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(min(65536, effective_max_bytes - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > effective_max_bytes:
                    raise ValueError("Image response exceeds maximum allowed byte size")
                chunks.append(chunk)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ValueError):
            raise exc.reason from exc
        raise

    image_bytes = b"".join(chunks)
    if not image_bytes:
        raise ValueError("Empty image response from URL")
    return image_bytes


def load_image_from_url(image_url: str) -> Image:
    image_bytes = get_image_bytes_from_url(image_url)
    return Image.from_bytes(image_bytes)


def validate_gcs_uri(
    image_uri: str, *, require_allowlist: bool = True
) -> tuple[str, str]:
    if not isinstance(image_uri, str) or not image_uri:
        raise ValueError("GCS URI must be a non-empty string")
    if any(ch in image_uri for ch in ("\r", "\n", "\x00", "\\", "?", "#")):
        raise ValueError("GCS URI contains disallowed characters")
    if not image_uri.startswith("gs://"):
        raise ValueError("GCS URI must start with gs://")

    remainder = image_uri[len("gs://") :]
    if "/" not in remainder:
        raise ValueError("GCS URI must have format gs://<bucket>/<object>")

    bucket, object_path = remainder.split("/", 1)
    if (
        not _GCS_BUCKET_PATTERN.match(bucket)
        or ".." in bucket
        or bucket.startswith("goog")
    ):
        raise ValueError("Invalid GCS bucket name in URI")

    if not object_path or object_path.startswith("/"):
        raise ValueError("Invalid GCS object path in URI")

    unquoted_path = urllib.parse.unquote(object_path)
    if "\\" in unquoted_path or "\x00" in unquoted_path:
        raise ValueError("Invalid characters in GCS object path")

    for path_variant in (object_path, unquoted_path):
        segments = path_variant.split("/")
        if any(seg in ("", ".", "..") for seg in segments):
            raise ValueError("Path traversal or empty segment is not allowed in GCS URI")

    raw_buckets = os.environ.get("ALLOWED_IMAGE_GCS_BUCKETS", "").strip()
    if not raw_buckets:
        raw_buckets = os.environ.get("ALLOWED_GCS_BUCKETS", "").strip()
    allowed_buckets = {b.strip() for b in raw_buckets.split(",") if b.strip()}

    if require_allowlist or allowed_buckets:
        if not allowed_buckets:
            raise ValueError(
                "GCS image access denied: ALLOWED_IMAGE_GCS_BUCKETS is not configured"
            )
        if bucket not in allowed_buckets:
            raise ValueError(f"GCS bucket '{bucket}' is not in the allowlist")

    raw_prefixes = os.environ.get("ALLOWED_IMAGE_GCS_PREFIXES", "").strip()
    if raw_prefixes:
        allowed_prefixes = [
            p.strip().lstrip("/") for p in raw_prefixes.split(",") if p.strip().lstrip("/")
        ]
        if allowed_prefixes:
            matched = False
            for prefix in allowed_prefixes:
                normalized_prefix = prefix.rstrip("/") + "/"
                if object_path.startswith(normalized_prefix) or object_path == prefix.rstrip("/"):
                    matched = True
                    break
            if not matched:
                raise ValueError("GCS object path is outside allowed prefixes")

    return bucket, object_path


# works only with public image
def get_url_from_gcs(gcs_uri: str) -> str:
    # converts gcs uri to url for image display.
    bucket, object_path = validate_gcs_uri(gcs_uri)
    quoted_object = urllib.parse.quote(object_path, safe="/")
    return f"https://storage.googleapis.com/{bucket}/{quoted_object}"


def from_url(image: str):
    image = load_image_from_url(image)  # convert to bytes
    return image


def from_gsc_uri(image_uri: str):
    validate_gcs_uri(image_uri)
    image_part = Part.from_uri(image_uri, mime_type="image/jpeg")
    return image_part


def _load_validated_image_source(image: str):
    if not isinstance(image, str) or not image.strip():
        raise ValueError("Image URI must be a non-empty string")
    if image.lower().startswith("gs://"):
        return from_gsc_uri(image)
    return from_url(image)


def content_generation(prompt: str, im):
    responses = ""
    try:
        responses = multimodal_model.generate_content(
            contents=[prompt, im],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
            },
        )
    except Exception as e:
        logging.error("Multimodal content generation failed: %s", e)
    return responses


def image_to_attributes(req: m.ImageRequest) -> m.ProductAttributes:
    prompt = """Provide the list of all the product attributes for the main
    product in the image in JSON format"""

    im = _load_validated_image_source(req.image)

    responses = content_generation(prompt, im)
    res = responses.text
    res = res.replace("```", "")
    res = res.replace("json", "")

    # This produces multiple models, NOT USEFUL for API calls.
    # had to create a parser to return consistent values

    attributes_json = json.loads(res.strip())

    if "product_attributes" not in attributes_json:
        response = m.parse_project_attributes_from_dict(attributes_json)
    else:
        # response = m.parse_list_to_dict(attributes_json.get('product_attributes'))
        response = m.parse_project_attributes_from_dict(
            attributes_json.get("product_attributes")
        )

    return response


def image_to_product_description(image: str) -> m.TextValue:
    prompt = """Write enriched product description for the main product in
    the image for retailer's product catalog"""

    im = _load_validated_image_source(image)
    responses = content_generation(prompt, im)
    res = ""
    for response in responses:
        res += response.candidates[0].content.parts[0].text
    desc = res.strip()

    return m.TextValue(text=desc)
