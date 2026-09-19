"""Query and embedding caching"""
import hashlib
import json
from typing import Optional, Any
from diskcache import Cache
from app.config.settings import settings
from app.utils.logger import logger


class CacheManager:
    """Manages caching for queries and embeddings"""
    
    def __init__(self):
        self.cache = Cache(str(settings.CACHE_DIR))
        self.ttl = 3600  # 1 hour
    
    def _get_key(self, query: str, **params) -> str:
        """Generate cache key from query and parameters"""
        key_data = {"query": query, **params}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_query_response(self, query: str, top_k: int = 5) -> Optional[dict]:
        """Get cached query response"""
        key = self._get_key(query, top_k=top_k)
        response = self.cache.get(key)
        if response:
            logger.debug(f"Cache hit for query: {query[:50]}...")
        return response
    
    def set_query_response(self, query: str, top_k: int, response: dict):
        """Cache query response"""
        key = self._get_key(query, top_k=top_k)
        self.cache.set(key, response, expire=self.ttl)
        logger.debug(f"Cached response for query: {query[:50]}...")
    
    def get_embedding(self, text: str) -> Optional[list]:
        """Get cached embedding"""
        key = self._get_key(text, type="embedding")
        return self.cache.get(key)
    
    def set_embedding(self, text: str, embedding: list):
        """Cache embedding"""
        key = self._get_key(text, type="embedding")
        self.cache.set(key, embedding, expire=self.ttl * 24)  # 24 hours
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "directory": str(settings.CACHE_DIR)
        }