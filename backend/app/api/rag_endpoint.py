from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.api.auth import get_db_user
from app.db.session import get_db
from app.db import crud, models
from app.schemas.query import QueryRequest, RagResponse
from app.rag.retrievers import RagPipeline

router = APIRouter()
rag_pipeline = RagPipeline()


@router.post("/query", response_model=RagResponse)
async def neo4j_rag_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user),
    x_retriever_type: Optional[str] = Header(None, alias="retriever-type")
):
    """
    Process a query and return a response in the specified RAG format.
    
    This endpoint supports a specific RAG format with standardized source handling:
    1. Each source includes its path, title, and snippets
    2. Up to 5 distinct sources are returned
    3. Sources are deduplicated by path
    4. Each source contains 1-2 verbatim snippets
    
    Returns:
        RagResponse: Answer and sources in the standardized RAG format
    """
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
    )
    
    return result
