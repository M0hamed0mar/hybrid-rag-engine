"""Cross-encoder reranking for precision improvement"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Tuple
from app.config.settings import settings
from app.utils.logger import logger
from app.core.chunk.models import DocumentChunk


class CrossEncoderReranker:
    """Rerank chunks using cross-encoder model"""
    
    def __init__(self):
        self.model_name = settings.RERANKER_MODEL
        self._model = None
        self._tokenizer = None
        self._device = None
        logger.info(f"Initializing reranker: {self.model_name}")
        self._load_model()  # Load immediately instead of lazy loading
    
    def _load_model(self):
        """Load the model and tokenizer"""
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            if torch.cuda.is_available():
                self._device = torch.device("cuda")
                self._model.to(self._device)
                logger.info(f"Reranker loaded on GPU")
            else:
                self._device = torch.device("cpu")
                logger.info(f"Reranker loaded on CPU")
            
            self._model.eval()
            logger.info(f"Reranker loaded successfully: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            self._model = None
            self._tokenizer = None
    
    @property
    def device(self):
        if self._device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return self._device
    
    @property
    def model(self):
        return self._model
    
    @property
    def tokenizer(self):
        return self._tokenizer
    
    def rerank(
        self,
        query: str,
        chunks: List[Tuple[DocumentChunk, float]],
        top_k: int = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Rerank chunks by cross-encoder relevance"""
        
        if not chunks:
            return []
        
        if top_k is None:
            top_k = len(chunks)
        
        # If model not loaded, return original chunks
        if self.model is None or self.tokenizer is None:
            logger.warning("Reranker not available, returning original chunks")
            return chunks[:top_k]
        
        try:
            # Prepare query-chunk pairs
            pairs = [(query, chunk.text_with_context) for chunk, _ in chunks]
            
            # Tokenize
            features = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            features = {k: v.to(self.device) for k, v in features.items()}
            
            # Get scores
            with torch.no_grad():
                scores = self.model(**features).logits
                relevance = torch.sigmoid(scores).cpu().numpy().flatten()
            
            # Combine with original scores (70% cross-encoder, 30% original)
            reranked = []
            for i, (chunk, orig_score) in enumerate(chunks):
                combined = 0.7 * float(relevance[i]) + 0.3 * orig_score
                reranked.append((chunk, combined))
            
            # Sort by combined score
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Reranked {len(chunks)} chunks, keeping top {top_k}")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return chunks[:top_k]