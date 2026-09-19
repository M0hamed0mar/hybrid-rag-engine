"""Pydantic schemas for API requests and responses"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ========== Request Models ==========

class QueryRequest(BaseModel):
    """RAG query request"""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    include_sources: bool = Field(default=True, description="Include source documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?",
                "top_k": 5,
                "include_sources": True
            }
        }


class URLIngestRequest(BaseModel):
    """URL ingestion request"""
    url: str = Field(..., description="Web URL to ingest")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article"
            }
        }


class TextIngestRequest(BaseModel):
    """Text ingestion request"""
    text: str = Field(..., min_length=1, description="Text content")
    source: str = Field(default="direct_input", description="Source identifier")


# ========== Response Models ==========

class SourceDocument(BaseModel):
    """Source document information"""
    chunk_id: str
    content: str
    source: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    relevance_score: float


class QueryResponse(BaseModel):
    """RAG query response"""
    query: str
    answer: str
    sources: List[SourceDocument]
    query_type: str
    total_chunks_retrieved: int
    processing_time_ms: float


class IngestResponse(BaseModel):
    """Document ingestion response"""
    success: bool
    document_id: str
    chunks_created: int
    message: str
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    vector_store_ready: bool
    bm25_ready: bool
    llm_ready: bool
    total_chunks: int
    cache_size: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ========== Document Management Models ==========

class DocumentInfo(BaseModel):
    """Document information"""
    source: str
    document_type: str
    chunks_count: int
    uploaded_at: Optional[str] = None  # Changed from required to optional


class DocumentsListResponse(BaseModel):
    """List of documents response"""
    documents: List[DocumentInfo]
    total: int


class DeleteDocumentRequest(BaseModel):
    """Delete document request"""
    source: str


class DeleteDocumentResponse(BaseModel):
    """Delete document response"""
    success: bool
    message: str
    deleted_chunks: int