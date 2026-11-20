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

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from auth import ROUTER_AUTH_DEPENDENCIES
from routers.categories import router as category_router
from routers.images import router as image_router
from routers.products import router as product_router
from routers.checks import router as checks_router

logger = logging.getLogger(__name__)

DEFAULT_CORS_ORIGINS = [
    "http://localhost:4000",
    "http://localhost:8080",
]


def get_allowed_cors_origins() -> list[str]:
    raw_origins = os.environ.get("ALLOWED_CORS_ORIGINS")
    if raw_origins is None:
        return list(DEFAULT_CORS_ORIGINS)

    parsed_origins: list[str] = []
    for candidate in raw_origins.split(","):
        origin = candidate.strip()
        if not origin:
            continue
        if origin == "*":
            logger.warning("Ignoring wildcard '*' in ALLOWED_CORS_ORIGINS")
            continue
        if not (origin.startswith("http://") or origin.startswith("https://")):
            logger.warning("Ignoring invalid origin in ALLOWED_CORS_ORIGINS: %s", origin)
            continue
        parsed_origins.append(origin)
    return parsed_origins


app = FastAPI()

origins = get_allowed_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    return response


app.include_router(checks_router, prefix="/hello", tags=["hello"])
app.include_router(
    category_router,
    prefix="/categories",
    tags=["categories"],
    dependencies=ROUTER_AUTH_DEPENDENCIES,
)
app.include_router(
    image_router,
    prefix="/images",
    tags=["images"],
    dependencies=ROUTER_AUTH_DEPENDENCIES,
)
app.include_router(
    product_router,
    prefix="/products",
    tags=["products"],
    dependencies=ROUTER_AUTH_DEPENDENCIES,
)
