from fastapi import APIRouter, Depends, HTTPException, Header, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
import json

from app.api.auth import get_db_user
from app.db.session import get_db
from app.db import crud, models
from app.schemas.query import QueryRequest
from app.schemas.ui_formats import UIRagResponse
from app.rag.retrievers import RagPipeline
from app.rag.ui_formatter import format_for_ui, enhance_with_metadata

router = APIRouter()

# Initialize RAG pipeline lazily to avoid startup issues
rag_pipeline = None

def get_rag_pipeline():
    global rag_pipeline
    if rag_pipeline is None:
        print("🔧 Initializing RAG pipeline...")
        rag_pipeline = RagPipeline()
    return rag_pipeline


@router.post("/query", response_model=Dict[str, Any])
async def ui_rag_query(
    query_request: QueryRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user),
    x_retriever_type: Optional[str] = Header(None, alias="retriever-type")
):
    """
    Process a query and return a response formatted for UI display.
    
    This endpoint returns a RAG response optimized for frontend display with:
    1. A clear, concise answer
    2. A collapsible sources panel with up to 5 sources
    3. Detailed metadata for each source
    
    Returns:
        JSON response with answer and UI-formatted sources panel
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
    
    # Process query with RAG pipeline
    pipeline = get_rag_pipeline()
    result = pipeline.search(
        query_request.query, 
        messages,
        retriever_type=retriever_type,
        use_rag_format=True
    )
    
    # Convert Pydantic model to dict
    result_dict = result.dict()
    
    # Format for UI display
    ui_response = format_for_ui(result_dict)
    
    # Enhance with additional metadata based on query
    enhanced_sources = enhance_with_metadata(ui_response.SOURCES_PANEL.items, query_request.query)
    ui_response.SOURCES_PANEL.items = enhanced_sources
    
    # Store the assistant response
    crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=ui_response.answer
    )
    
    # Convert to dict for JSONResponse
    response_dict = ui_response.dict()
    
    # Set content type to ensure proper JSON formatting
    response.headers["Content-Type"] = "application/json"
    
    return response_dict
