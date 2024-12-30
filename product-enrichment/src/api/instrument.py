#   Copyright 2022 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from fastapi import status, FastAPI

def register(app: FastAPI):
    @app.get("/readiness_check", status_code=status.HTTP_200_OK)
    def readiness_check():
        return {"status": "ok"}

    @app.get("/liveness_check", status_code=status.HTTP_200_OK)
    def liveness_check():
        return {"status": "ok"}