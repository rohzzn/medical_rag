from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.api.auth import get_db_user
from app.db.session import get_db
from app.db import crud, models
from app.schemas.query import (
    Conversation, 
    ConversationCreate, 
    QueryRequest, 
    QueryResult, 
    MessageCreate, 
    MessageWithSources,
    RagResponse
)
from app.rag.retrievers import RagPipeline

router = APIRouter()

rag_pipeline = RagPipeline()


@router.get("/conversations", response_model=List[Conversation])
def get_all_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user)
):
    """Get all conversations for the current user."""
    conversations = crud.get_conversations(db, user_id=current_user.id, skip=skip, limit=limit)
    return conversations


@router.post("/conversations", response_model=Conversation)
def create_new_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user)
):
    """Create a new conversation."""
    return crud.create_conversation(db, user_id=current_user.id, title=conversation.title)


@router.get("/conversations/{conversation_id}", response_model=Conversation)
def get_conversation_with_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user)
):
    """Get a conversation with all its messages."""
    conversation = crud.get_conversation(db, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    return conversation


@router.post("/query", response_model=QueryResult)
async def process_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user),
    x_retriever_type: Optional[str] = Header(None, alias="retriever-type")
):
    """Process a query and return the answer with sources."""
    # Get the retriever type from header or environment
    retriever_type = x_retriever_type or os.getenv("RETRIEVER_TYPE", "hybrid")
    
    # Validate retriever type
    if retriever_type not in ["hybrid", "vector_cypher", "vector"]:
        retriever_type = "hybrid"  # Default to hybrid if invalid
    
    # Get or create a conversation
    conversation_id = query_request.conversation_id
    if not conversation_id:
        # Create a new conversation with the query as title
        conversation = crud.create_conversation(
            db, 
            user_id=current_user.id, 
            title=query_request.query[:50] + "..." if len(query_request.query) > 50 else query_request.query
        )
        conversation_id = conversation.id
    else:
        # Check if conversation exists and belongs to user
        conversation = crud.get_conversation(db, conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    # Store the user query
    crud.create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=query_request.query
    )
    
    # Get conversation history
    messages = crud.get_messages(db, conversation_id=conversation_id)
    
    # Process query with RAG pipeline, passing the retriever type
    result = rag_pipeline.search(
        query_request.query, 
        messages,
        retriever_type=retriever_type
    )
    
    # Store the assistant response with sources
    sources_data = [{"source_path": source.source_path, "source_name": source.source_name} for source in result["sources"]]
    crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=result["answer"],
        sources=sources_data
    )
    
    return QueryResult(
        answer=result["answer"],
        sources=result["sources"],
        conversation_id=conversation_id
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageWithSources])
def get_messages_for_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user)
):
    """Get all messages for a conversation."""
    # Check if conversation exists and belongs to user
    conversation = crud.get_conversation(db, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    # Get messages
    messages = crud.get_messages(db, conversation_id=conversation_id)
    return messages


@router.post("/rag-assistant", response_model=RagResponse)
async def rag_assistant_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user),
    x_retriever_type: Optional[str] = Header(None, alias="retriever-type")
):
    """Process a query and return a response in the RAG Assistant format."""
    # Get the retriever type from header or environment
    retriever_type = x_retriever_type or os.getenv("RETRIEVER_TYPE", "hybrid")
    
    # Validate retriever type
    if retriever_type not in ["hybrid", "vector_cypher", "vector"]:
        retriever_type = "hybrid"  # Default to hybrid if invalid
    
    # Get or create a conversation
    conversation_id = query_request.conversation_id
    if not conversation_id:
        # Create a new conversation with the query as title
        conversation = crud.create_conversation(
            db, 
            user_id=current_user.id, 
            title=query_request.query[:50] + "..." if len(query_request.query) > 50 else query_request.query
        )
        conversation_id = conversation.id
    else:
        # Check if conversation exists and belongs to user
        conversation = crud.get_conversation(db, conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    # Store the user query
    crud.create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=query_request.query
    )
    
    # Get conversation history
    messages = crud.get_messages(db, conversation_id=conversation_id)
    
    # Process query with RAG pipeline, passing the retriever type and use_rag_format=True
    result = rag_pipeline.search(
        query_request.query, 
        messages,
        retriever_type=retriever_type,
        use_rag_format=True
    )
    
    # Store the assistant response
    crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=result.answer
        # Note: We don't store sources in the database for RAG assistant format
    )
    
    return result