from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class MessageBase(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class MessageCreate(MessageBase):
    pass


class Source(BaseModel):
    source_path: str
    source_name: str
    paper_id: Optional[str] = None
    paper_url: Optional[str] = None
    content: Optional[str] = None


class MessageWithSources(MessageBase):
    id: int
    created_at: datetime
    sources: Optional[List[Source]] = None

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2


class Message(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2


class ConversationBase(BaseModel):
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2


class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None


class QueryResult(BaseModel):
    answer: str
    sources: List[Source]
    conversation_id: int