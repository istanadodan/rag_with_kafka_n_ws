from typing import Dict, Any
from schemas.base import AppBaseModel


class SourceDocument(AppBaseModel):
    page_content: str
    metadata: Dict[str, Any]


class QdrantPayload(AppBaseModel):
    source: str
    metadata: Dict[str, Any]


class ParentDocumentDto(AppBaseModel):
    id: int
    content: str
    mdata: str
