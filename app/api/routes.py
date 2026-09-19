"""FastAPI routes for RAG system"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid
from app.api.schemas import (
    QueryRequest, IngestResponse, HealthResponse,
    URLIngestRequest, TextIngestRequest,
    DocumentsListResponse, DocumentInfo, DeleteDocumentResponse
)
from app.core.pipeline import RAGPipeline
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter()
pipeline = RAGPipeline()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    stats = pipeline.get_stats()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        vector_store_ready=stats["vector_store_ready"],
        bm25_ready=stats["bm25_ready"],
        llm_ready=stats["llm_ready"],
        total_chunks=stats["total_chunks"],
        cache_size=stats["cache_stats"]["size"]
    )


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    try:
        allowed_extensions = ['.pdf', '.docx', '.pptx', '.png', '.jpg', '.jpeg']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        file_id = str(uuid.uuid4())[:8]
        save_path = settings.UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = pipeline.ingest_document(file_path=save_path)
        save_path.unlink()
        
        return IngestResponse(**result)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: URLIngestRequest):
    try:
        result = pipeline.ingest_document(url=request.url)
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"URL ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(request: TextIngestRequest):
    try:
        result = pipeline.ingest_document(text=request.text, source=request.source)
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Text ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query(request: QueryRequest):
    try:
        result = pipeline.query(request.query, top_k=request.top_k)
        return {
            "query": result["query"],
            "answer": result["answer"],
            "source_note": result.get("source_note"),
            "query_type": result["query_type"],
            "processing_time_ms": result["processing_time_ms"]
        }
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    return pipeline.get_stats()


@router.delete("/cache")
async def clear_cache():
    pipeline.cache.clear()
    return {"message": "Cache cleared successfully"}


@router.get("/documents", response_model=DocumentsListResponse)
async def list_documents():
    stats = pipeline.get_stats()
    documents = stats.get("documents", [])
    return DocumentsListResponse(
        documents=[DocumentInfo(**doc) for doc in documents],
        total=len(documents)
    )


@router.delete("/documents/{source:path}", response_model=DeleteDocumentResponse)
async def delete_document(source: str):
    try:
        success = pipeline.delete_document(source)
        if success:
            return DeleteDocumentResponse(
                success=True,
                message=f"Document '{source}' deleted successfully",
                deleted_chunks=0
            )
        else:
            return DeleteDocumentResponse(
                success=False,
                message=f"Document '{source}' not found",
                deleted_chunks=0
            )
    except Exception as e:
        return DeleteDocumentResponse(
            success=False,
            message=f"Error deleting document: {str(e)}",
            deleted_chunks=0
        )


@router.delete("/clear-all")
async def clear_all_data():
    try:
        pipeline.vector_store.index = None
        pipeline.vector_store.chunks = []
        pipeline.vector_store._save()
        
        pipeline.bm25_index.bm25 = None
        pipeline.bm25_index.chunks = []
        pipeline.bm25_index.tokenized_corpus = []
        pipeline.bm25_index._save()
        
        pipeline.cache.clear()
        pipeline.clear_conversation()
        
        return {
            "success": True,
            "message": "All data cleared successfully",
            "deleted_chunks": 0
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "deleted_chunks": 0
        }


@router.get("/conversation/history")
async def get_conversation_history():
    return {"history": pipeline.get_conversation_history()}


@router.delete("/conversation/history")
async def clear_conversation_history():
    pipeline.clear_conversation()
    return {"message": "Conversation history cleared"}