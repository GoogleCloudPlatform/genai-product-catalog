from datetime import datetime
from typing import Optional

from sqlalchemy import Engine
from common.model import GeminiPrompt
from fastapi import status, FastAPI, Response
from pydantic import BaseModel
from db.prompts import PromptsDao

class PromptRequest(BaseModel):
    name: str
    prompt: Optional[str]


def register(app: FastAPI, engine: Engine):

    dao = PromptsDao(engine)

    @app.post("/prompts", status_code=status.HTTP_201_CREATED)
    def post(prompt: GeminiPrompt):
        dao.create(prompt)

    @app.put("/prompts/:id", status_code=status.HTTP_202_ACCEPTED)
    def put(id: int, prompt: GeminiPrompt, response: Response):
        if id == prompt.id:
            return dao.update(prompt)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return None

    @app.get("/prompts/:name")
    def get(name: str, response: Response):
        out = dao.find_by_name(name)
        if out is None:
            response.status_code = status.HTTP_404_NOT_FOUND
        return out

