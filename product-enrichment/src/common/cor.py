from enum import StrEnum, auto
from typing import Optional, Any, Dict
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel, CheckConstraint
from datetime import datetime

class HttpVerb(StrEnum):
    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()

class CommandOrder(StrEnum):
    BEGIN = auto(),
    BODY = auto()
    END = auto()

class PersistedCommand(SQLModel, table=False):
    __table_args__ = (
        UniqueConstraint("name"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime = Field(default=datetime.now())
    updated: datetime = Field(default=datetime.now())
    deleted: Optional[datetime] = Field(default=None)
    name: str = Field(max_length=255)


class HttpEntryPointCommand(PersistedCommand, table=True):
    """A user defined HTTP entry point and associated workflow ID"""
    __tablename__ = 'cmd_http_entry_point'
    __table_args__ = (
        UniqueConstraint("entry_point_uri", "entry_point_verb"),
        CheckConstraint("entry_point_verb IN ('GET', 'POST', 'PUT', 'DELETE')"),
    )

    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BEGIN

    entry_point_uri: str = Field(max_length=128)
    entry_point_verb: HttpVerb = Field()
    override_context_id: str = Field(max_length=128)
    processor_id: str = Field()


class PubSubEntryPointCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_pubsub_entry_points'
    __table_args__ = (
        UniqueConstraint("topic_name", "processor_name")
    )
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BEGIN

    topic_name: str = Field(max_length=128)
    override_context_id: str = Field(max_length=128)
    processor_id: str = Field()

class HttpCallbackCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_http_callbacks'
    __table_args__ = (
        CheckConstraint("callback_verb IN ('GET', 'POST', 'PUT', 'DELETE')"),
    )
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.END

    callback_uri: str = Field(max_length=128)
    callback_verb: HttpVerb = Field()
    headers: Dict[str, str] = Field(default={})



class GeminiPromptCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_gemini_prompts'
    prompt: str = Field()
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BODY


