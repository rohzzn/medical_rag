import re
from typing import List, Dict, Any, Optional
from app.schemas.query import RagResponse, RagSource

def format_rag_response(answer: str, retriever_items: List[Any], retriever_type: str) -> RagResponse:
    """
    Format the RAG response according to the RAG Assistant requirements.
    
    Args:
        answer: The generated answer text
        retriever_items: List of retriever items with content
        retriever_type: The type of retriever used ("vector", "vector_cypher", or "hybrid")
        
    Returns:
        RagResponse: Formatted response with answer and sources
    """
    # If no retriever items, return a default response
    if not retriever_items or len(retriever_items) == 0:
        return RagResponse(
            answer="I don't have enough evidence in the current knowledge base to answer.",
            sources=[]
        )
    
    # Process based on retriever type
    if retriever_type == "vector":
        sources = process_vector_results(retriever_items)
    else:
        # Both hybrid_cypher and vector_cypher use the same format
        sources = process_cypher_results(retriever_items)
    
    # Deduplicate sources by path
    unique_sources = {}
    for source in sources:
        if source["path"] not in unique_sources:
            unique_sources[source["path"]] = source
            
    # Get the top 5 sources (or fewer if not available)
    top_sources = list(unique_sources.values())[:5]
    
    # Create RagSource objects
    rag_sources = []
    for source in top_sources:
        rag_sources.append(
            RagSource(
                path=source["path"],
                title=source["title"],
                url=None,  # URL should be null per requirements
                snippets=source["snippets"]
            )
        )
    
    return RagResponse(
        answer=answer,
        sources=rag_sources
    )

def process_vector_results(items: List[Any]) -> List[Dict[str, Any]]:
    """
    Process Vector retriever results.
    
    Args:
        items: List of retriever items where each item.content contains JSON with "text" and "source2"
        
    Returns:
        List of source dictionaries with path, title, and snippets
    """
    sources = []
    
    for item in items:
        try:
            # Convert string representation to dictionary if needed
            content = item.content
            if isinstance(content, str):
                # Try to extract source2 and text using regex
                source_match = re.search(r"source2['\":\s]+([^'\",\s]+)", content)
                text_match = re.search(r"text['\":\s]+([^'\"]+)", content)
                
                source_path = source_match.group(1) if source_match else None
                text = text_match.group(1) if text_match else None
                
                if not source_path or not text:
                    continue
            else:
                # Assume it's already a dictionary-like object
                source_path = getattr(content, "source2", None)
                text = getattr(content, "text", None)
                
                if not source_path or not text:
                    continue
            
            # Get the basename for title
            title = source_path.split("/")[-1].split("\\")[-1]
            
            # Create source dictionary
            source = {
                "path": source_path,
                "title": title,
                "snippets": [extract_snippet(text)]
            }
            
            sources.append(source)
            
        except Exception as e:
            print(f"Error processing vector item: {e}")
            continue
    
    return sources

def process_cypher_results(items: List[Any]) -> List[Dict[str, Any]]:
    """
    Process HybridCypher or VectorCypher retriever results.
    
    Args:
        items: List of retriever items where each item.content contains truncated_chunk_texts and chunk_sources
        
    Returns:
        List of source dictionaries with path, title, and snippets
    """
    sources = []
    seen_paths = set()
    
    for item in items:
        try:
            content_str = str(item.content)
            
            # Extract truncated_chunk_texts
            chunk_texts_match = re.search(r"truncated_chunk_texts=['\"](.*?)['\"]", content_str, re.DOTALL)
            if not chunk_texts_match:
                continue
                
            chunk_texts_str = chunk_texts_match.group(1)
            chunk_texts = re.split(r'\\n---\\n', chunk_texts_str)
            
            # Extract chunk_sources
            chunk_sources_match = re.search(r"chunk_sources=['\"](.*?)['\"]", content_str, re.DOTALL)
            if not chunk_sources_match:
                continue
                
            chunk_sources_str = chunk_sources_match.group(1)
            chunk_sources = re.split(r'\\n---\\n', chunk_sources_str)
            
            # Match texts with sources
            for i, source_path in enumerate(chunk_sources):
                if i >= len(chunk_texts) or source_path in seen_paths:
                    continue
                    
                seen_paths.add(source_path)
                
                # Get the basename for title
                title = source_path.split("/")[-1].split("\\")[-1]
                
                # Create source dictionary
                source = {
                    "path": source_path,
                    "title": title,
                    "snippets": [extract_snippet(chunk_texts[i])]
                }
                
                sources.append(source)
                
        except Exception as e:
            print(f"Error processing cypher item: {e}")
            continue
    
    return sources

def extract_snippet(text: str, max_chars: int = 500) -> str:
    """
    Extract a meaningful snippet from the text, not exceeding max_chars.
    
    Args:
        text: Source text to extract from
        max_chars: Maximum characters for the snippet
        
    Returns:
        Formatted snippet string
    """
    if not text:
        return ""
        
    # Clean up the text
    cleaned_text = text.strip()
    
    # If text is already short enough, return it
    if len(cleaned_text) <= max_chars:
        return cleaned_text
    
    # Try to truncate at sentence boundary
    truncated = cleaned_text[:max_chars]
    last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    
    if last_period > max_chars / 2:  # Only if we don't lose too much text
        truncated = truncated[:last_period + 1]
    
    return truncated