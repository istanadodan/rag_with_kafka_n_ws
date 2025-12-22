from typing import Dict, Any
from models.base import AppBaseModel


class SourceDocument(AppBaseModel):
    page_content: str
    metadata: Dict[str, Any]


class QdrantPayload(AppBaseModel):
    source: str
    metadata: Dict[str, Any]
