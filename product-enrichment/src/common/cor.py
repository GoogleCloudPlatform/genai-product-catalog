from enum import StrEnum, auto
from typing import Optional
from sqlalchemy import UniqueConstraint

from sqlmodel import Field, SQLModel, CheckConstraint, Column, JSON
from datetime import datetime
from sqlalchemy_continuum import make_versioned

make_versioned(user_cls=None)


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
    __versioned__ = {}
    __table_args__ = (
        UniqueConstraint("name"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = Field(default=None, nullable=False)
    created: datetime = Field(default=datetime.now())
    updated: datetime = Field(default=datetime.now())
    deleted: Optional[datetime] = Field(default=None)
    name: str = Field(max_length=255)


class EntryPointHTTPCommand(PersistedCommand, table=True):
    """A user defined HTTP entry point and associated workflow ID"""
    __tablename__ = 'cmd_ep_http'
    __table_args__ = (
        UniqueConstraint("entry_point_uri", "entry_point_verb", "processor_id"),
        CheckConstraint("entry_point_verb IN ('GET', 'POST', 'PUT', 'DELETE')"),
    )

    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BEGIN

    entry_point_uri: str = Field(max_length=128)
    entry_point_verb: HttpVerb = Field()
    override_context_id: str = Field(max_length=128)
    processor_id: str = Field()


class EntryPointPubSubCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_ep_pubsub'
    __table_args__ = (
        UniqueConstraint("topic_name", "processor_id"),
    )
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BEGIN

    topic_name: str = Field(max_length=128)
    override_context_id: str = Field(max_length=128)
    processor_id: str = Field()


class CallbackHTTPCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_cb_http'
    __table_args__ = (
        CheckConstraint("callback_verb IN ('GET', 'POST', 'PUT', 'DELETE')"),
    )
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.END

    callback_uri: str = Field(max_length=128)
    callback_verb: HttpVerb = Field()
    headers: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True


class GeminiPromptCommand(PersistedCommand, table=True):
    __tablename__ = 'cmd_gemini_prompts'
    model_name: str = Field(max_length=128)
    prompt: str = Field()
    @staticmethod
    def get_order() -> CommandOrder:
        return CommandOrder.BODY


