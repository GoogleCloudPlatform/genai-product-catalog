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

import api.prompts as prompts
import api.product as product
import api.instrument as instrument

app = FastAPI()

def start(cfg: Config, host: str, port: int, reload: bool):
    engine = cfg.postgres.get_engine(echo=True)
    instrument.register(app)
    prompts.register(app, engine)
    product.register(app, engine)

    """Starts the server in dev mode"""
    uvicorn.run("api.server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    config = Config("env.toml")
    start(config, "127.0.0.1", 8000, reload=True)