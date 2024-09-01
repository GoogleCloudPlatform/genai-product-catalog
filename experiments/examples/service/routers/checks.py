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

from fastapi import APIRouter
from models.checks_model import Liveliness, Status

router = APIRouter()


@router.get("/readiness_check")
def readiness_check() -> Status:
    return Status(status="ready")


@router.get("/liveness_check")
def liveness_check() -> Liveliness:
    return Liveliness(message="ready")
