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
import uvicorn
from common.config import Config
from fastapi import FastAPI

import api.product as product
import api.instrument as instrument

config = Config("env.toml")
engine = config.postgres.get_engine(echo=True)

app = FastAPI()

instrument.register(app)
product.register(app, engine)

def start(host: str, port: int, reload: bool):
    """Starts the server in dev mode"""
    uvicorn.run("api.server:app", host=host, port=port, reload=reload)

def dev():
    """Starts the server in prod mode"""
    start("127.0.0.1", 8000, True)

def prod():
    """Starts the server in prod mode"""
    start("0.0.0.0", 8080, False)

if __name__ == "__main__":
    dev()