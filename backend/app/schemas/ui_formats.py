from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal


class ExpandedSourceView(BaseModel):
    """Expanded view of a source with detailed information."""
    exact_passage: str
    location: Optional[str] = None
    why_it_supports: str


class SourceItem(BaseModel):
    """A source item with collapsed and expanded views."""
    title: str
    source: str
    expanded: ExpandedSourceView


class UISettings(BaseModel):
    """UI display settings for the sources panel."""
    max_width: str = "100%"
    padding: str = "1em"
    overflow: str = "hidden"
    text_wrap: str = "normal"
    scroll_inside_expanded: bool = True


class SourcesPanel(BaseModel):
    """The collapsible sources panel."""
    title: str
    ui: UISettings
    items: List[SourceItem] = []


class UIRagResponse(BaseModel):
    """The answer with UI-optimized sources panel."""
    answer: str
    SOURCES_PANEL: SourcesPanel
