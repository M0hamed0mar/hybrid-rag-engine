"""Hybrid retrieval combining vector and BM25 search"""
from typing import List, Tuple
from app.core.store.vector import VectorStore
from app.core.store.bm25 import BM25Index
from app.core.embed.encoder import EmbeddingEncoder
from app.core.chunk.models import DocumentChunk
from app.utils.logger import logger


class HybridRetriever:
    """Combine dense and sparse retrieval methods"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_index: BM25Index,
        embedder: EmbeddingEncoder
    ):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.embedder = embedder
        
        # Fusion weights
        self.vector_weight = 0.5
        self.bm25_weight = 0.5
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        vector_weight: float = None,
        bm25_weight: float = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve using both methods and combine results"""
        
        v_weight = vector_weight or self.vector_weight
        b_weight = bm25_weight or self.bm25_weight
        
        # Vector search
        query_embedding = self.embedder.encode(query)
        vector_results = self.vector_store.similarity_search(query_embedding, top_k * 2)
        
        # BM25 search
        bm25_results = self.bm25_index.search(query, top_k * 2)
        
        # Combine scores
        combined = {}
        chunk_map = {}
        
        # Add vector results
        for result in vector_results:
            chunk_id = result['id']
            chunk = DocumentChunk(
                id=chunk_id,
                content=result['content'],
                source=result['metadata'].get('source', ''),
                document_type=result['metadata'].get('document_type', ''),
                chunk_index=result['metadata'].get('chunk_index', 0),
                page_number=result['metadata'].get('page_number'),
                section_title=result['metadata'].get('section_title')
            )
            chunk_map[chunk_id] = chunk
            combined[chunk_id] = combined.get(chunk_id, 0) + v_weight * result['score']
        
        # Add BM25 results
        for chunk, score in bm25_results:
            chunk_map[chunk.id] = chunk
            combined[chunk.id] = combined.get(chunk.id, 0) + b_weight * score
        
        # Sort and return top_k
        sorted_results = sorted(
            [(chunk_map[cid], combined[cid]) for cid in combined],
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"Hybrid retrieval returned {len(sorted_results[:top_k])} results")
        return sorted_results[:top_k]