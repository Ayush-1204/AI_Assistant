from typing import Any, Literal

from pydantic import BaseModel, Field


class BasePresentationNode(BaseModel):
    id: str
    type: str

class HeadingNode(BasePresentationNode):
    type: Literal["Heading"] = "Heading"
    text: str
    level: int = 1

class ParagraphNode(BasePresentationNode):
    type: Literal["Paragraph"] = "Paragraph"
    text: str

class BulletListNode(BasePresentationNode):
    type: Literal["BulletList"] = "BulletList"
    items: list[str]

class NumberedListNode(BasePresentationNode):
    type: Literal["NumberedList"] = "NumberedList"
    items: list[str]

class NewsCardNode(BasePresentationNode):
    type: Literal["NewsCard"] = "NewsCard"
    title: str
    summary: str
    source: str
    url: str | None = None
    imageUrl: str | None = None
    imageUrls: list[str] = Field(default_factory=list)
    publishedAt: str | None = None   # ISO date string or human-readable
    category: str | None = None      # e.g. "Technology", "Business"

class WeatherCardNode(BasePresentationNode):
    type: Literal["WeatherCard"] = "WeatherCard"
    location: str
    temperature_c: float
    condition: str
    forecast: list[dict[str, Any]] = Field(default_factory=list)

class ComparisonTableNode(BasePresentationNode):
    type: Literal["ComparisonTable"] = "ComparisonTable"
    headers: list[str]
    rows: list[list[str]]

class CodeBlockNode(BasePresentationNode):
    type: Literal["CodeBlock"] = "CodeBlock"
    language: str
    code: str

class ImageGalleryNode(BasePresentationNode):
    type: Literal["ImageGallery"] = "ImageGallery"
    images: list[dict[str, str]]  # list of {"url": "...", "alt": "..."}

class TimelineNode(BasePresentationNode):
    type: Literal["Timeline"] = "Timeline"
    events: list[dict[str, str]] # list of {"time": "...", "title": "...", "description": "..."}

class AccordionNode(BasePresentationNode):
    type: Literal["Accordion"] = "Accordion"
    title: str
    content: str
