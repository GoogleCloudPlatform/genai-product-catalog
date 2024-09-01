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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.categories import router as category_router
from routers.images import router as image_router
from routers.products import router as product_router
from routers.checks import router as checks_router


app = FastAPI()

origins = [
    "*",
    "http://localhost:4000",
    "http://localhost:8080",
    "https://retail-shared-demos.uc.r.appspot.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(checks_router, prefix="/hello", tags=["hello"])
app.include_router(category_router, prefix="/categories", tags=["categories"])
app.include_router(image_router, prefix="/images", tags=["images"])
app.include_router(product_router, prefix="/products", tags=["products"])
