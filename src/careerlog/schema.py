from datetime import date
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    date: date
    text: str                      # what you did, in plain words
    tags: list[str] = []           # e.g. ["python", "ml"]
    source: Literal["manual", "github", "n8n"] = "manual"
    link: str | None = None        # PR / repo / doc URL, used later as evidence