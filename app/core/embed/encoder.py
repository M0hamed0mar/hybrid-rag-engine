"""Vector embedding encoder using sentence-transformers"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.config.settings import settings
from app.utils.logger import logger


class EmbeddingEncoder:
    """Generate dense vector embeddings for text"""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._model = None
        self._dimension = 384
        logger.info(f"Initializing embedding model: {self.model_name}")
    
    @property
    def model(self):
        """Lazy load model"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Dimension: {self._dimension}")
        return self._model
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings for text(s)"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # For cosine similarity
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings
    
    def encode_chunks(self, chunks: List) -> np.ndarray:
        """Encode list of DocumentChunk objects"""
        texts = [chunk.text_with_context for chunk in chunks]
        return self.encode(texts)