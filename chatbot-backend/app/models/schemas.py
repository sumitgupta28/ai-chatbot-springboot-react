from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    id: int
    filename: str
    contentType: Optional[str] = None
    fileSize: Optional[int] = None
    uploadTime: datetime
    chunkCount: int


class VectorStoreInfo(BaseModel):
    filename: str
    contentLength: int
    contentPreview: str


class SearchResult(BaseModel):
    filename: str
    similarity: float
    contentPreview: str


class VerifyResponse(BaseModel):
    status: str
    documentsCount: int
    documents: List[VectorStoreInfo]


class SearchResponse(BaseModel):
    query: str
    hitsFound: int
    results: List[SearchResult]
