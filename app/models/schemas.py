from pydantic import BaseModel, Field
from typing import List, Optional

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_stored: int
    status: str

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    top_k: Optional[int] = Field(default=None, description="Number of source chunks to retrieve")

class SourceCitation(BaseModel):
    document: str
    page: Optional[int] = None
    chunk_preview: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    cached: bool
    latency_ms: float

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    uploaded_at: str
    chunk_count: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
