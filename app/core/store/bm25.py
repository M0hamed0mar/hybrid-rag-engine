"""BM25 keyword index for hybrid retrieval"""
from rank_bm25 import BM25Okapi
from typing import List, Tuple
import pickle
from pathlib import Path
import nltk
from nltk.tokenize import word_tokenize
from app.config.settings import settings
from app.utils.logger import logger
from app.core.chunk.models import DocumentChunk

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class BM25Index:
    """BM25 keyword search index"""
    
    def __init__(self):
        self.index_path = settings.CHROMA_DIR / "bm25_index.pkl"
        self.bm25 = None
        self.chunks: List[DocumentChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self._load()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25"""
        tokens = word_tokenize(text.lower())
        return [t for t in tokens if t.isalnum() and len(t) > 1]
    
    def _get_chunk_text(self, chunk: DocumentChunk) -> str:
        """Get formatted chunk text"""
        if chunk.section_title:
            return f"{chunk.section_title} {chunk.content}"
        return chunk.content
    
    def _save(self):
        """Save index to disk"""
        if self.bm25 is None:
            return
        
        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'corpus': self.tokenized_corpus,
                'chunks': [chunk.to_dict() for chunk in self.chunks]
            }, f)
        
        logger.info(f"BM25 index saved: {len(self.chunks)} chunks")
    
    def _load(self):
        """Load index from disk"""
        if not self.index_path.exists():
            logger.info("No existing BM25 index")
            return
        
        with open(self.index_path, 'rb') as f:
            data = pickle.load(f)
            self.tokenized_corpus = data['corpus']
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            self.chunks = [DocumentChunk.from_dict(c) for c in data['chunks']]
        
        logger.info(f"BM25 index loaded: {len(self.chunks)} chunks")
    
    def add_chunks(self, chunks: List[DocumentChunk]):
        """Add chunks to index"""
        if not chunks:
            return
        
        new_tokenized = [self._tokenize(self._get_chunk_text(c)) for c in chunks]
        self.tokenized_corpus.extend(new_tokenized)
        self.chunks.extend(chunks)
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        self._save()
        
        logger.info(f"Added {len(chunks)} chunks to BM25 index")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Search by keyword relevance"""
        if not self.bm25 or not self.chunks:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.chunks[idx], float(scores[idx])))
        
        return results
    
    def get_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks)