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
import http.client
import ipaddress
import json
import logging
import os
import posixpath
import re
import socket
import ssl
import typing
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)

DEFAULT_FETCH_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MiB
DEFAULT_MAX_IMAGE_URLS = 20
DEFAULT_MAX_WORKERS = 8

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
_ALLOWED_IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

headers = {
    "User-Agent": "genai-product-catalog-adk-image-downloader/1.0",
    "Accept": "image/jpeg,image/png,image/webp,image/gif;q=0.9,*/*;q=0.1",
}


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


def _get_max_image_urls() -> int:
    raw = os.environ.get("IMAGE_DOWNLOADER_MAX_URLS", "").strip()
    if not raw:
        return DEFAULT_MAX_IMAGE_URLS
    try:
        max_urls = int(raw)
    except ValueError as exc:
        raise ValueError("Invalid IMAGE_DOWNLOADER_MAX_URLS configuration") from exc
    if max_urls <= 0 or max_urls > 100:
        raise ValueError("IMAGE_DOWNLOADER_MAX_URLS must be between 1 and 100")
    return max_urls


def _get_allowed_image_domains() -> tuple[str, ...]:
    raw = os.environ.get("ALLOWED_IMAGE_DOMAINS", "").strip()
    if not raw:
        return ()
    domains: list[str] = []
    for entry in raw.split(","):
        cleaned = entry.strip().lstrip(".").rstrip(".").lower()
        if cleaned:
            domains.append(cleaned)
    return tuple(domains)


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
        or normalized.endswith(".corp")
    ):
        raise ValueError("Image URL hostname is not allowed")

    try:
        ipaddress.ip_address(normalized.split("%")[0])
        is_ip_literal = True
    except ValueError:
        is_ip_literal = False

    if is_ip_literal:
        _validate_ip_address(normalized)

    allowed_domains = _get_allowed_image_domains()
    if allowed_domains:
        if not any(
            normalized == domain or normalized.endswith(f".{domain}")
            for domain in allowed_domains
        ):
            raise ValueError("Image URL hostname is not in ALLOWED_IMAGE_DOMAINS")

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
        _validate_ip_address(sockaddr[0])
        validated.append((family, socktype, proto, sockaddr))
    return validated


def validate_https_image_url(
    image_url: str,
) -> tuple[
    str, str, int, list[tuple[socket.AddressFamily, socket.SocketKind, int, tuple]]
]:
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
    if port != 443:
        raise ValueError("Only standard HTTPS port 443 is allowed for image URLs")

    validated_addrs = _resolve_and_validate_host(parsed.hostname, port)
    return image_url, parsed.hostname, port, validated_addrs


def _detect_image_mime_type(data: bytes) -> Optional[str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _sanitize_artifact_filename(url: str, index: int, mime_type: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    raw_name = posixpath.basename(urllib.parse.unquote(parsed.path).rstrip("/"))
    cleaned = _SAFE_FILENAME_CHARS.sub("_", raw_name).lstrip("._")
    cleaned = cleaned[:80]
    if not cleaned:
        ext = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }.get(mime_type, "bin")
        cleaned = f"image_{index}.{ext}"
    return f"downloaded_image_{cleaned}"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError(
            f"HTTP redirects are not allowed for image URLs (HTTP {code})"
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        *,
        expected_host: str,
        validated_addrs: list[
            tuple[socket.AddressFamily, socket.SocketKind, int, tuple]
        ],
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
        validated_addrs: list[
            tuple[socket.AddressFamily, socket.SocketKind, int, tuple]
        ],
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
    validated_addrs: list[
        tuple[socket.AddressFamily, socket.SocketKind, int, tuple]
    ],
) -> urllib.request.OpenerDirector:
    opener = urllib.request.OpenerDirector()
    opener.add_handler(_PinnedHTTPSHandler(expected_host, validated_addrs))
    opener.add_handler(_NoRedirectHandler())
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    return opener


def fetch_validated_image(
    url: str,
    *,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> tuple[bytes, str]:
    validated_url, hostname, _, validated_addrs = validate_https_image_url(url)
    effective_timeout = _get_fetch_timeout() if timeout is None else timeout
    effective_max_bytes = _get_max_image_bytes() if max_bytes is None else max_bytes

    opener = _build_safe_https_opener(hostname, validated_addrs)
    req = urllib.request.Request(
        validated_url,
        method="GET",
        headers=dict(headers),
    )
    try:
        with opener.open(req, timeout=effective_timeout) as response:
            response = typing.cast(http.client.HTTPResponse, response)
            raw_content_type = (
                response.headers.get("Content-Type", "") if response.headers else ""
            )
            media_type = raw_content_type.split(";", 1)[0].strip().lower()
            if media_type and media_type not in _ALLOWED_IMAGE_MIME_TYPES:
                raise ValueError("Image response returned a disallowed Content-Type")

            content_length = (
                response.headers.get("Content-Length") if response.headers else None
            )
            if content_length is not None:
                try:
                    declared_len = int(content_length)
                except ValueError as exc:
                    raise ValueError(
                        "Invalid Content-Length header in image response"
                    ) from exc
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

    detected_mime = _detect_image_mime_type(image_bytes)
    if detected_mime is None:
        raise ValueError("Downloaded content is not a supported image format")

    return image_bytes, detected_mime


def _parse_product_image_urls(raw_product_images: Any) -> list[str]:
    if isinstance(raw_product_images, str):
        cleaned = raw_product_images.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json") :]
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```") :]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
        parsed = json.loads(cleaned.strip())
    elif isinstance(raw_product_images, list):
        parsed = raw_product_images
    else:
        raise ValueError("product_images_urls must be a JSON array of URL strings")

    if not isinstance(parsed, list):
        raise ValueError("product_images_urls must be a list of URL strings")

    max_urls = _get_max_image_urls()
    urls = [item for item in parsed if isinstance(item, str)]
    return urls[:max_urls]


async def download_and_add_images_to_artifacts(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    Downloads images from a list of validated public HTTPS URLs in parallel
    and adds them to the context artifacts.

    Args:
        callback_context: The tool context from the Gemini ADK agent.
                 It is expected to contain a key 'product_images_urls' with a JSON
                 list of HTTPS image URLs.

    Returns:
        A Content summary indicating how many images were downloaded.
    """
    raw_product_images = callback_context.state.get("product_images_urls")
    logger.debug("Running image downloader callback for %s", callback_context.agent_name)
    if not raw_product_images:
        return types.Content(
            parts=[types.Part(text="skipped due to state.")],
            role="model",
        )

    try:
        product_images = _parse_product_image_urls(raw_product_images)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Failed to parse product_images_urls: %s", exc)
        return types.Content(
            parts=[types.Part(text="Skipped image download due to invalid URL list.")],
            role="model",
        )

    if not product_images:
        return types.Content(
            parts=[types.Part(text="Successfully downloaded and added 0/0 images to artifacts.")],
            role="model",
        )

    def download_image(index: int, url: str) -> Dict[str, Any]:
        """Validates and downloads a single public HTTPS image."""
        try:
            image_bytes, mime_type = fetch_validated_image(url)
            return {
                "index": index,
                "url": url,
                "content": image_bytes,
                "mime_type": mime_type,
                "error": None,
            }
        except (ValueError, urllib.error.URLError, http.client.HTTPException, OSError) as exc:
            logger.warning("Rejected or failed image download for URL #%d: %s", index, exc)
            return {
                "index": index,
                "url": url,
                "content": None,
                "mime_type": None,
                "error": "Image validation or download failed",
            }

    max_workers = min(DEFAULT_MAX_WORKERS, len(product_images))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_image, idx, url): url
            for idx, url in enumerate(product_images)
        }
        downloaded_images = [
            future.result() for future in concurrent.futures.as_completed(future_to_url)
        ]

    successful_downloads = 0
    for result in downloaded_images:
        if result["content"] and result["mime_type"]:
            file_name = _sanitize_artifact_filename(
                result["url"], result["index"], result["mime_type"]
            )
            image_part = types.Part.from_bytes(
                data=result["content"], mime_type=result["mime_type"]
            )
            await callback_context.save_artifact(file_name, image_part)
            successful_downloads += 1

    return types.Content(
        parts=[
            types.Part(
                text=(
                    f"Successfully downloaded and added "
                    f"{successful_downloads}/{len(product_images)} images to artifacts."
                )
            )
        ],
        role="model",
    )
