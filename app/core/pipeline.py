"""Complete RAG pipeline orchestrator"""
import time
from typing import List, Tuple
from app.utils.logger import logger
from app.utils.cache import CacheManager
from app.core.chunk.models import DocumentChunk
from app.core.ingest import DocumentLoader
from app.core.chunk import SemanticChunker
from app.core.embed import EmbeddingEncoder
from app.core.store import VectorStore, BM25Index
from app.core.retrieve import QueryRouter, QueryExpander, HybridRetriever, ReciprocalRankFusion
from app.core.rerank import CrossEncoderReranker
from app.core.generate import ContextBuilder, GeminiClient


class RAGPipeline:
    """Orchestrates the complete RAG pipeline"""
    
    def __init__(self):
        # Initialize all components
        self.loader = DocumentLoader()
        self.chunker = SemanticChunker()
        self.embedder = EmbeddingEncoder()
        self.vector_store = VectorStore()
        self.bm25_index = BM25Index()
        self.query_router = QueryRouter()
        self.query_expander = QueryExpander()
        self.hybrid_retriever = HybridRetriever(
            self.vector_store, self.bm25_index, self.embedder
        )
        self.rrf_fusion = ReciprocalRankFusion()
        self.reranker = CrossEncoderReranker()
        self.context_builder = ContextBuilder()
        self.llm = GeminiClient()
        self.cache = CacheManager()
        
        logger.info("RAG Pipeline initialized successfully")
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.llm.clear_history()
    
    def get_conversation_history(self):
        """Get conversation history"""
        return self.llm.get_history()
    
    def ingest_document(self, file_path=None, url=None, text=None, source=None) -> dict:
        """Ingest a document into the system"""
        start_time = time.time()
        
        # Load document
        if file_path:
            result = self.loader.load_file(file_path)
            doc_id = file_path.stem
        elif url:
            result = self.loader.load_url(url)
            doc_id = url.split('/')[-1][:50]
        elif text:
            result = self.loader.load_text(text, source or "direct_input")
            doc_id = "text_input"
        else:
            raise ValueError("Must provide file_path, url, or text")
        
        # Create chunks
        chunks = self.chunker.chunk_document(
            text=result['text'],
            source=result['metadata']['source'],
            document_type=result['metadata']['document_type']
        )
        
        if not chunks:
            return {
                "success": False,
                "document_id": doc_id,
                "chunks_created": 0,
                "message": "No content extracted",
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        
        # Generate embeddings
        embeddings = self.embedder.encode_chunks(chunks)
        
        # Store in vector DB
        self.vector_store.add_chunks(chunks, embeddings)
        
        # Store in BM25 index
        self.bm25_index.add_chunks(chunks)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "document_id": doc_id,
            "chunks_created": len(chunks),
            "message": f"Successfully ingested {result['metadata']['document_type']}",
            "processing_time_ms": elapsed_ms
        }
    
    def query(self, query: str, top_k: int = 5) -> dict:
        """Process a user query through the complete RAG pipeline"""
        start_time = time.time()
        
        # Check cache (skip if conversation has history)
        cached = self.cache.get_query_response(query, top_k)
        if cached and len(self.llm.get_history()) == 0:
            cached["processing_time_ms"] = (time.time() - start_time) * 1000
            return cached
        
        # Step 1: Route query
        query_type = self.query_router.classify(query)
        params = self.query_router.get_retrieval_params(query_type)
        
        # Step 2: Expand query
        expanded_queries = self.query_expander.expand(query)
        
        # Step 3: Retrieve for each expansion
        all_results = []
        for q in expanded_queries:
            results = self.hybrid_retriever.retrieve(q, top_k=params['top_k'] * 2)
            all_results.append(results)
        
        # Step 4: Fuse results with RRF
        fused_results = self.rrf_fusion.fuse(all_results)
        
        # Step 5: Rerank if needed
        if params.get('use_reranker', True):
            reranked = self.reranker.rerank(query, fused_results, top_k=top_k)
        else:
            reranked = fused_results[:top_k]
        
        # Step 6: Build context
        context = self.context_builder.build_context(reranked)
        
        # Check if we have meaningful context
        has_context = len(reranked) > 0 and context != "No relevant context found."
        
        # Step 7: Generate answer (includes conversation history)
        answer, source_note = self.llm.generate(context, query, has_context=has_context)
        
        response = {
            "query": query,
            "answer": answer,
            "source_note": source_note,
            "query_type": query_type.value,
            "total_chunks_retrieved": len(reranked),
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        # Cache response only if no conversation history
        if len(self.llm.get_history()) == 0:
            self.cache.set_query_response(query, top_k, response)
        
        return response
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        documents = self._get_unique_sources()
        return {
            "total_chunks": self.vector_store.get_count(),
            "bm25_chunks": self.bm25_index.get_count(),
            "total_documents": len(documents),
            "documents": documents,
            "cache_stats": self.cache.get_stats(),
            "vector_store_ready": True,
            "bm25_ready": self.bm25_index.bm25 is not None,
            "llm_ready": self.llm.enabled
        }

    def _get_unique_sources(self) -> List[dict]:
        """Get unique document sources with metadata"""
        sources = {}
        for chunk in self.vector_store.chunks:
            if chunk.source not in sources:
                sources[chunk.source] = {
                    "source": chunk.source,
                    "document_type": chunk.document_type,
                    "chunks_count": 0
                }
            sources[chunk.source]["chunks_count"] += 1
        return list(sources.values())
    
    def delete_document(self, source: str) -> bool:
        """Delete all chunks from a document"""
        try:
            # Filter out chunks from this source
            chunks_to_keep = []
            indices_to_keep = []
            
            for i, chunk in enumerate(self.vector_store.chunks):
                if chunk.source != source:
                    chunks_to_keep.append(chunk)
                    indices_to_keep.append(i)
            
            if len(chunks_to_keep) == len(self.vector_store.chunks):
                return False
            
            # Update vector store
            self.vector_store.chunks = chunks_to_keep
            self.vector_store._rebuild_index()
            
            # Update BM25
            self.bm25_index.delete_document(source)
            
            logger.info(f"Deleted document: {source}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False