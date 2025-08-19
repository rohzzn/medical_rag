from typing import List, Dict, Any, Optional
import re

from app.schemas.query import Source, RagResponse, RagSource
from app.schemas.ui_formats import UIRagResponse, SourcesPanel, SourceItem, ExpandedSourceView, UISettings


def format_for_ui(rag_response: Dict[str, Any]) -> UIRagResponse:
    """
    Format a RAG response into a UI-friendly format with collapsible sources panel.
    
    Args:
        rag_response: Dictionary containing answer and sources
        
    Returns:
        UIRagResponse: Formatted response with answer and SOURCES_PANEL
    """
    answer = rag_response.get("answer", "")
    sources = rag_response.get("sources", [])
    
    # Count valid sources
    source_count = min(len(sources), 5)
    
    # Create the sources panel title
    panel_title = f"Sources ({source_count})"
    
    # Process sources into UI items
    items = []
    seen_titles = set()
    
    for source in sources[:5]:  # Limit to 5 sources
        # Extract source info
        path = source.get("path", "")
        title = source.get("title", "")
        snippets = source.get("snippets", [])
        
        # Skip duplicates (by title)
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        # Create readable title
        readable_title = make_readable_title(title)
        
        # Combine snippets into a single passage (if multiple)
        exact_passage = combine_snippets(snippets)
        
        # Create source item
        item = SourceItem(
            title=readable_title,
            source=path,
            expanded=ExpandedSourceView(
                exact_passage=exact_passage,
                location="Document excerpt",  # Default location if not available
                why_it_supports="Contains relevant information that directly addresses the query."  # Default justification
            )
        )
        
        items.append(item)
    
    # Create the sources panel
    sources_panel = SourcesPanel(
        title=panel_title,
        ui=UISettings(),
        items=items
    )
    
    # Return the complete UI response
    return UIRagResponse(
        answer=answer,
        SOURCES_PANEL=sources_panel
    )


def make_readable_title(title: str) -> str:
    """Make a readable title from a filename or path."""
    # Remove file extension if present
    title = re.sub(r'\.\w+$', '', title)
    
    # Replace underscores and hyphens with spaces
    title = title.replace('_', ' ').replace('-', ' ')
    
    # Title case the result
    title = ' '.join(word.capitalize() for word in title.split())
    
    return title


def combine_snippets(snippets: List[str]) -> str:
    """Combine multiple snippets into a single passage."""
    if not snippets:
        return ""
        
    if len(snippets) == 1:
        return snippets[0]
    
    # Join snippets with ellipsis separator
    return " […] ".join(snippets)


def enhance_with_metadata(sources: List[SourceItem], query: str) -> List[SourceItem]:
    """
    Enhance sources with additional metadata like location and support justification.
    
    Args:
        sources: List of source dictionaries
        query: Original user query
        
    Returns:
        Enhanced list of sources
    """
    # Extract key terms from the query
    query_terms = set(query.lower().split())
    key_terms = {term for term in query_terms if len(term) > 3}
    
    for source in sources:
        # Extract title and snippets
        title = source.title
        # We'll use the exact_passage from the expanded view
        snippet_text = source.expanded.exact_passage
        
        # Determine a more specific location if possible
        if "clinical" in title.lower() or "trial" in title.lower():
            source.expanded.location = "Clinical research findings"
        elif "review" in title.lower():
            source.expanded.location = "Literature review"
        elif "guideline" in title.lower():
            source.expanded.location = "Clinical guidelines"
        
        # Generate a more specific justification
        snippet_text_lower = snippet_text.lower()
        
        if any(term in snippet_text_lower for term in key_terms):
            source.expanded.why_it_supports = f"Directly addresses {', '.join(key_terms)} mentioned in the query."
        elif "treatment" in query.lower() and any(term in snippet_text_lower for term in ["treatment", "therapy", "medication"]):
            source.expanded.why_it_supports = "Provides treatment information relevant to the query."
        elif "pathophysiology" in query.lower() and any(term in snippet_text_lower for term in ["mechanism", "pathology", "cause"]):
            source.expanded.why_it_supports = "Explains pathophysiological mechanisms relevant to the query."
        elif "variant" in query.lower() and any(term in snippet_text_lower for term in ["variant", "type", "form"]):
            source.expanded.why_it_supports = "Describes disease variants mentioned in the query."
    
    return sources
