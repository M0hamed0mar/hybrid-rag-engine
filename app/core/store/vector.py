"""Vector database using FAISS"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any
from app.config.settings import settings
from app.utils.logger import logger
from app.core.chunk.models import DocumentChunk


class VectorStore:
    """FAISS vector storage for embeddings"""
    
    def __init__(self, collection_name: str = "rag_documents"):
        self.collection_name = collection_name
        self.index_path = settings.CHROMA_DIR / f"{collection_name}.faiss"
        self.metadata_path = settings.CHROMA_DIR / f"{collection_name}.pkl"
        
        self.index = None
        self.chunks: List[DocumentChunk] = []
        self.dimension = 384
        
        settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _get_chunk_text(self, chunk: DocumentChunk) -> str:
        if chunk.section_title:
            return f"## {chunk.section_title}\n\n{chunk.content}"
        return chunk.content
    
    def _save(self):
        if self.index is None:
            return
        
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump({
                'chunks': [chunk.to_dict() for chunk in self.chunks]
            }, f)
        
        logger.info(f"FAISS index saved: {len(self.chunks)} chunks")
    
    def _load(self):
        if not self.index_path.exists() or not self.metadata_path.exists():
            logger.info("No existing FAISS index found. Creating new one.")
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunks = []
            return
        
        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.chunks = [DocumentChunk.from_dict(c) for c in data['chunks']]
            logger.info(f"FAISS index loaded: {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunks = []
    
    def _rebuild_index(self):
        """Rebuild FAISS index from current chunks (requires re-embedding)"""
        if not self.chunks:
            self.index = faiss.IndexFlatIP(self.dimension)
            self._save()
            return
        
        logger.warning("Rebuilding index requires re-embedding all chunks")
        # For now, just reset
        self.index = faiss.IndexFlatIP(self.dimension)
        self._save()
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: np.ndarray):
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings length mismatch")
        
        faiss.normalize_L2(embeddings)
        
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
        
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self._save()
        
        logger.info(f"Added {len(chunks)} chunks. Total: {len(self.chunks)}")
    
    def similarity_search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        formatted = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                chunk = self.chunks[idx]
                formatted.append({
                    "id": chunk.id,
                    "content": self._get_chunk_text(chunk),
                    "metadata": {
                        "source": chunk.source,
                        "document_type": chunk.document_type,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number or 0,
                        "section_title": chunk.section_title or ""
                    },
                    "score": float(distances[0][i])
                })
        
        return formatted
    
    def get_count(self) -> int:
        return len(self.chunks)