from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.security import get_password_hash, verify_password
from app.db import models
from app.schemas import user as user_schema
from app.schemas import query as query_schema


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: user_schema.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Conversation]:
    return db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id
    ).order_by(models.Conversation.updated_at.desc()).offset(skip).limit(limit).all()


def get_conversation(db: Session, conversation_id: int) -> Optional[models.Conversation]:
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()


def create_conversation(db: Session, user_id: int, title: Optional[str] = None) -> models.Conversation:
    db_conversation = models.Conversation(user_id=user_id, title=title)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_messages(db: Session, conversation_id: int) -> List[models.Message]:
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at).all()


def create_message(
    db: Session, 
    conversation_id: int, 
    role: str, 
    content: str,
    sources: Optional[List[Dict[str, Any]]] = None
) -> models.Message:
    db_message = models.Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message