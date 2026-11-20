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


"""Invoke Vertex Embedding API."""

import base64 as base64_lib
import binascii
import logging
import os
import re
import urllib.parse
from functools import cache
from typing import NamedTuple, Optional, Sequence

from google.cloud import aiplatform
from google.protobuf import struct_pb2

from google.cloud.ml.applied.config import Config

_GCS_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]$")
_MAX_BASE64_IMAGE_CHARS = 20 * 1024 * 1024  # ~15 MiB decoded


def validate_gcs_uri(
    image_uri: str, *, require_allowlist: bool = True
) -> tuple[str, str]:
    """Validate a gs:// URI and enforce bucket/prefix allowlists."""
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

    if not allowed_buckets:
        for section in (Config.SECTION_GCS, Config.SECTION_DEFAULT):
            try:
                cfg_bucket = Config.value(section, "bucket_name")
            except (KeyError, TypeError):
                cfg_bucket = None
            if isinstance(cfg_bucket, str) and cfg_bucket.strip():
                allowed_buckets.add(cfg_bucket.strip())

    if require_allowlist or allowed_buckets:
        if not allowed_buckets:
            raise ValueError(
                "GCS image access denied: ALLOWED_IMAGE_GCS_BUCKETS is not configured"
            )
        if bucket not in allowed_buckets:
            raise ValueError("GCS bucket is not in the allowlist")

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


def _validate_base64_image(encoded_image: str) -> str:
    if not isinstance(encoded_image, str) or not encoded_image.strip():
        raise ValueError("Base64 image payload must be a non-empty string")
    if len(encoded_image) > _MAX_BASE64_IMAGE_CHARS:
        raise ValueError("Base64 image payload exceeds maximum allowed size")
    try:
        decoded = base64_lib.b64decode(encoded_image, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image payload") from exc
    if not decoded:
        raise ValueError("Base64 image payload must not be empty")
    return encoded_image


class EmbeddingResponse(NamedTuple):
    text_embedding: Sequence[float]
    image_embedding: Sequence[float]


class EmbeddingPredictionClient:
    """Wrapper around Prediction Service Client."""

    def __init__(self):
        project = Config.value(Config.SECTION_PROJECT, "id")
        location = Config.value(Config.SECTION_PROJECT, "location")
        api_regional_endpoint = Config.value(Config.SECTION_PROJECT, "endpoint")

        client_options = {"api_endpoint": api_regional_endpoint}
        # Initialize client that will be used to create and send requests.
        # This client only needs to be created once, and can be reused for multiple requests.
        self.client = aiplatform.gapic.PredictionServiceClient(
            client_options=client_options
        )
        self.location = location
        self.project = project

    def get_embedding(
        self,
        text: Optional[str] = None,
        image: Optional[str] = None,
        base64: bool = False,
    ):
        """Invoke Vertex multimodal embedding API.

        You can pass text and/or image. If neither is passed will raise exception

        Args:
          text: text to embed
          image: can be local file path, GCS URI or base64 encoded image
          base64: True indicates image is base64. False (default) will be
            interpreted as image path (either local or GCS)
        Returns:
        named tuple with the following attributes:
          text_embedding: 1408 dimension vector of type Sequence[float]
          image_embedding: 1408 dimension vector of type Sequence[float] OR None if
            no image provide
        """
        if not text and not image:
            raise ValueError("At least one of text or image_bytes must be specified.")

        instance = struct_pb2.Struct()
        if text:
            if len(text) >= 1024:
                logging.warning(
                    "Text must be less than 1024 characters. Truncating text."
                )
                text = text[:1023]
            instance.fields["text"].string_value = text

        if image:
            image_struct = instance.fields["image"].struct_value
            if base64:
                image_struct.fields["bytesBase64Encoded"].string_value = (
                    _validate_base64_image(image)
                )
            else:
                validate_gcs_uri(image, require_allowlist=True)
                image_struct.fields["gcsUri"].string_value = image

        instances = [instance]

        # TODO - THIS SHOULD NOT BE HARD CODED

        endpoint = (
            f"projects/{self.project}/locations/{self.location}"
            "/publishers/google/models/multimodalembedding@001"
        )
        response = self.client.predict(endpoint=endpoint, instances=instances)

        text_embedding = None
        if text:
            text_emb_value = response.predictions[0]["textEmbedding"]
            text_embedding = [v for v in text_emb_value]

        image_embedding = None
        if image:
            image_emb_value = response.predictions[0]["imageEmbedding"]
            image_embedding = [v for v in image_emb_value]

        return EmbeddingResponse(
            text_embedding=text_embedding, image_embedding=image_embedding
        )


@cache
def get_client(project):
    return EmbeddingPredictionClient()


def embed(
    text: str,
    image: Optional[str] = None,
    base64: bool = False,
    project: str = Config.value("project", "id"),
) -> EmbeddingResponse:
    """Invoke vertex multimodal embedding API.

    Args:
      text: text to embed
      image: can be local file path, GCS URI or base64 encoded image
      base64: True indicates image is base64. False (default) will be
          interpreted as image path (either local or GCS)
      project: GCP Project ID

    Returns:
      named tuple with the following attributes:
        text_embedding: 1408 dimension vector of type Sequence[float]
        image_embedding: 1408 dimension vector of type Sequence[float] OR None if
          no image provide
    """
    client = get_client(project)
    response = client.get_embedding(text=text, image=image, base64=base64)
    return response
