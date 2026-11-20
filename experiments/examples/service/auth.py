# Copyright 2024 Google LLC
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

"""Authentication, authorization, and tenant-scoping dependencies for FastAPI."""

from collections import OrderedDict
import hashlib
import hmac
import logging
import os
import re
import threading
from typing import NamedTuple, Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token as google_id_token

from google.cloud.ml.applied.images import image_to_text

logger = logging.getLogger(__name__)

# Tenant IDs may not start/end with '_' or contain '__' so f"{tenant}__{product}"
# is injective and cannot collide across tenants.
TENANT_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]|_(?!_)){0,62}[A-Za-z0-9]$|^[A-Za-z0-9]$"
)
PRODUCT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
CATEGORY_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9 _&/.,+-]{1,128}$")
TENANT_NAMESPACE_SEPARATOR = "__"
_MAX_CATEGORY_ITEMS = 16
_MAX_TRACKED_PRODUCTS = 50000
_VALID_GOOGLE_ISSUERS = frozenset(
    {"https://accounts.google.com", "accounts.google.com"}
)

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticatedPrincipal(NamedTuple):
    tenant_id: str
    subject: str


_ownership_lock = threading.Lock()
_product_owners: OrderedDict[str, set[str]] = OrderedDict()


def reset_product_ownership_registry() -> None:
    with _ownership_lock:
        _product_owners.clear()


def _constant_time_equals(provided: str, expected: str) -> bool:
    provided_digest = hashlib.sha256(provided.encode("utf-8")).digest()
    expected_digest = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(provided_digest, expected_digest)


def _get_default_tenant_id() -> str:
    default_tenant = os.environ.get("DEFAULT_TENANT_ID", "default").strip() or "default"
    if not TENANT_ID_PATTERN.fullmatch(default_tenant) or "__" in default_tenant:
        raise HTTPException(
            status_code=503, detail="Invalid DEFAULT_TENANT_ID configuration"
        )
    return default_tenant


def _load_configured_api_keys() -> list[tuple[str, str]]:
    default_tenant = _get_default_tenant_id()
    entries: list[tuple[str, str]] = []

    raw_keys = os.environ.get("SERVICE_API_KEYS", "").strip()
    if raw_keys:
        for item in raw_keys.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                tenant_part, token_part = item.split(":", 1)
                tenant_id = tenant_part.strip()
                secret = token_part.strip()
            else:
                tenant_id = default_tenant
                secret = item

            if (
                not tenant_id
                or not secret
                or not TENANT_ID_PATTERN.fullmatch(tenant_id)
                or TENANT_NAMESPACE_SEPARATOR in tenant_id
            ):
                logger.error("Ignoring malformed entry in SERVICE_API_KEYS")
                continue
            entries.append((tenant_id, secret))

    single_token = os.environ.get("API_AUTH_TOKEN", "").strip()
    if single_token:
        entries.append((default_tenant, single_token))

    return entries


def _load_allowed_oidc_audiences() -> list[str]:
    raw = os.environ.get("ALLOWED_OIDC_AUDIENCE", "").strip()
    if not raw:
        return []
    return [aud.strip() for aud in raw.split(",") if aud.strip()]


def _match_api_key(
    candidate_token: str, configured_keys: list[tuple[str, str]]
) -> Optional[AuthenticatedPrincipal]:
    if not candidate_token or not configured_keys:
        return None
    matched_tenant: Optional[str] = None
    for idx, (tenant_id, expected_secret) in enumerate(configured_keys):
        if _constant_time_equals(candidate_token, expected_secret):
            if matched_tenant is None:
                matched_tenant = tenant_id
                matched_subject = f"apikey:{tenant_id}:{idx}"
    if matched_tenant is not None:
        return AuthenticatedPrincipal(tenant_id=matched_tenant, subject=matched_subject)
    return None


def _sanitize_oidc_tenant(raw_identifier: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-]", "_", raw_identifier)
    cleaned = re.sub(r"_+", "_", cleaned)[:48].strip("_")
    if not cleaned:
        digest = hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()[:16]
        return f"oidc_{digest}"
    return f"oidc_{cleaned}"


def _load_allowed_oidc_emails() -> set[str]:
    raw = os.environ.get("ALLOWED_OIDC_EMAILS", "").strip()
    if not raw:
        return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _verify_oidc_bearer_token(
    token: str, allowed_audiences: list[str]
) -> Optional[AuthenticatedPrincipal]:
    if not token or not allowed_audiences:
        return None

    allowed_emails = _load_allowed_oidc_emails()
    if not allowed_emails:
        logger.error(
            "ALLOWED_OIDC_AUDIENCE is configured without ALLOWED_OIDC_EMAILS; failing closed."
        )
        raise HTTPException(
            status_code=503,
            detail="OIDC identity allowlist is not configured",
        )

    request_adapter = google_auth_requests.Request()
    claims: Optional[dict] = None
    for audience in allowed_audiences:
        try:
            verified = google_id_token.verify_oauth2_token(
                token, request_adapter, audience=audience
            )
            if verified:
                claims = dict(verified)
                break
        except Exception as exc:
            logger.debug("OIDC token verification failed for audience %s: %s", audience, exc)

    if not claims:
        return None

    issuer = claims.get("iss")
    if issuer not in _VALID_GOOGLE_ISSUERS:
        logger.warning("Rejected OIDC token with unexpected issuer: %s", issuer)
        return None

    subject = str(claims.get("sub") or "").strip()
    if not subject:
        return None

    email = str(claims.get("email") or "").strip().lower()
    if not claims.get("email_verified") or email not in allowed_emails:
        raise HTTPException(
            status_code=403, detail="Authenticated identity is not authorized"
        )

    if os.environ.get("TRUST_OIDC_TENANT_CLAIM", "").strip().lower() == "true":
        claim_tenant = str(claims.get("tenant_id") or "").strip()
        if (
            claim_tenant
            and TENANT_ID_PATTERN.fullmatch(claim_tenant)
            and TENANT_NAMESPACE_SEPARATOR not in claim_tenant
        ):
            return AuthenticatedPrincipal(tenant_id=claim_tenant, subject=f"oidc:{subject}")

    return AuthenticatedPrincipal(
        tenant_id=_sanitize_oidc_tenant(subject),
        subject=f"oidc:{subject}",
    )


def require_authenticated_principal(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
) -> AuthenticatedPrincipal:
    configured_keys = _load_configured_api_keys()
    allowed_audiences = _load_allowed_oidc_audiences()

    if not configured_keys and not allowed_audiences:
        raise HTTPException(
            status_code=503,
            detail="Service authentication is not configured",
        )

    raw_auth_header = request.headers.get("Authorization")
    if raw_auth_header and bearer_credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header; expected Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if bearer_credentials is None and not api_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key_principal: Optional[AuthenticatedPrincipal] = None
    if api_key is not None:
        api_key_principal = _match_api_key(api_key.strip(), configured_keys)
        if api_key_principal is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    bearer_principal: Optional[AuthenticatedPrincipal] = None
    if bearer_credentials is not None:
        if bearer_credentials.scheme.lower() != "bearer" or not bearer_credentials.credentials:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = bearer_credentials.credentials.strip()
        bearer_principal = _match_api_key(token, configured_keys)
        if bearer_principal is None and allowed_audiences:
            bearer_principal = _verify_oidc_bearer_token(token, allowed_audiences)
        if bearer_principal is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if (
        api_key_principal is not None
        and bearer_principal is not None
        and api_key_principal.tenant_id != bearer_principal.tenant_id
    ):
        raise HTTPException(
            status_code=401,
            detail="Conflicting authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    principal = bearer_principal or api_key_principal
    assert principal is not None

    explicit_tenant_header = request.headers.get("X-Tenant-ID")
    if explicit_tenant_header is not None:
        if explicit_tenant_header.strip() != principal.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Cross-tenant access is forbidden",
            )

    return principal


ROUTER_AUTH_DEPENDENCIES = [
    Security(bearer_scheme),
    Security(api_key_header),
    Depends(require_authenticated_principal),
]


def _parse_and_verify_product_id(
    raw_product_id: Optional[str], principal: AuthenticatedPrincipal
) -> str:
    if not isinstance(raw_product_id, str) or not raw_product_id:
        raise ValueError("Product ID is required")

    clean_id = raw_product_id
    if ":" in raw_product_id:
        owner_prefix, remainder = raw_product_id.split(":", 1)
        if not TENANT_ID_PATTERN.fullmatch(owner_prefix) or not PRODUCT_ID_PATTERN.fullmatch(
            remainder
        ):
            raise ValueError("Product ID must match [A-Za-z0-9_-]{1,128}")
        if owner_prefix != principal.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Cross-tenant product access is forbidden",
            )
        clean_id = remainder
    elif TENANT_NAMESPACE_SEPARATOR in raw_product_id:
        owner_prefix, remainder = raw_product_id.split(TENANT_NAMESPACE_SEPARATOR, 1)
        if not TENANT_ID_PATTERN.fullmatch(owner_prefix) or not PRODUCT_ID_PATTERN.fullmatch(
            remainder
        ):
            raise ValueError("Product ID must match [A-Za-z0-9_-]{1,128}")
        if owner_prefix != principal.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Cross-tenant product access is forbidden",
            )
        clean_id = remainder
    else:
        if not PRODUCT_ID_PATTERN.fullmatch(raw_product_id):
            raise ValueError("Product ID must match [A-Za-z0-9_-]{1,128}")

    return clean_id


def scope_product_id_for_upsert(
    raw_product_id: Optional[str],
    principal: AuthenticatedPrincipal,
    *,
    is_update: bool = False,
) -> str:
    clean_id = _parse_and_verify_product_id(raw_product_id, principal)
    scoped_id = f"{principal.tenant_id}{TENANT_NAMESPACE_SEPARATOR}{clean_id}"
    with _ownership_lock:
        owner = _product_owners.get(scoped_id)
        if owner is None:
            if len(_product_owners) >= _MAX_TRACKED_PRODUCTS:
                _product_owners.popitem(last=False)
            _product_owners[scoped_id] = {principal.tenant_id}
        else:
            if principal.tenant_id not in owner:
                raise HTTPException(
                    status_code=403,
                    detail="Cross-tenant product update is forbidden",
                )
            _product_owners.move_to_end(scoped_id)

    return scoped_id


def scope_product_id_for_delete(
    raw_product_id: Optional[str], principal: AuthenticatedPrincipal
) -> str:
    clean_id = _parse_and_verify_product_id(raw_product_id, principal)
    scoped_id = f"{principal.tenant_id}{TENANT_NAMESPACE_SEPARATOR}{clean_id}"
    with _ownership_lock:
        owner = _product_owners.get(scoped_id)
        if owner is not None:
            if principal.tenant_id not in owner:
                raise HTTPException(
                    status_code=403,
                    detail="Cross-tenant product deletion is forbidden",
                )
            _product_owners.pop(scoped_id, None)

    return scoped_id


def validate_product_categories(categories: Optional[list[str]]) -> list[str]:
    if not categories:
        return []
    if len(categories) > _MAX_CATEGORY_ITEMS:
        raise ValueError(f"At most {_MAX_CATEGORY_ITEMS} category filters are allowed")
    validated: list[str] = []
    for cat in categories:
        if not isinstance(cat, str) or not CATEGORY_VALUE_PATTERN.fullmatch(cat):
            raise ValueError("Invalid category value")
        validated.append(cat)
    return validated


def validate_optional_product_image_uri(image_uri: Optional[str]) -> Optional[str]:
    if image_uri is None or image_uri == "":
        return image_uri
    if not isinstance(image_uri, str):
        raise ValueError("Invalid image_uri value")
    if not image_uri.startswith("gs://"):
        raise ValueError("Product image_uri must be a valid gs:// URI")
    image_to_text.validate_gcs_uri(image_uri, require_allowlist=True)
    return image_uri
