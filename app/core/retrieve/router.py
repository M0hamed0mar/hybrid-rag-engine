"""Query classification and routing"""
from enum import Enum
import re
from app.utils.logger import logger


class QueryType(str, Enum):
    """Types of user queries"""
    FACTUAL = "factual"
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"
    TABLE = "table"


class QueryRouter:
    """Classify user queries to determine retrieval strategy"""
    
    # Pattern definitions
    FACTUAL_PATTERNS = [
        r'\b(what|who|when|where|how many|how much)\b',
        r'\b(define|explain|list|name|identify)\b',
        r'\b(is|are|was|were|does|do|did)\b',
    ]
    
    SUMMARIZATION_PATTERNS = [
        r'\b(summarize|summary|overview|gist|brief|tl;dr)\b',
        r'\b(what is the main|key points|in short)\b',
    ]
    
    REASONING_PATTERNS = [
        r'\b(why|how|compare|contrast|difference|similar|versus|vs)\b',
        r'\b(analyze|evaluate|assess|justify)\b',
        r'\b(because|since|due to|as a result)\b',
    ]
    
    TABLE_PATTERNS = [
        r'\b(table|chart|figure|diagram|matrix|grid)\b',
        r'\b(rows?|columns?|data|statistics)\b',
    ]
    
    def classify(self, query: str) -> QueryType:
        """Classify query type based on patterns"""
        query_lower = query.lower()
        
        scores = {
            QueryType.FACTUAL: 0,
            QueryType.SUMMARIZATION: 0,
            QueryType.REASONING: 0,
            QueryType.TABLE: 0,
        }
        
        for pattern in self.FACTUAL_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.FACTUAL] += 1
        
        for pattern in self.SUMMARIZATION_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.SUMMARIZATION] += 1
        
        for pattern in self.REASONING_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.REASONING] += 1
        
        for pattern in self.TABLE_PATTERNS:
            if re.search(pattern, query_lower):
                scores[QueryType.TABLE] += 1
        
        # Get highest scoring type
        max_score = max(scores.values())
        
        if max_score == 0:
            return QueryType.FACTUAL
        
        # Handle ties based on query length
        max_types = [t for t, s in scores.items() if s == max_score]
        
        if len(max_types) > 1 and len(query) > 100:
            if QueryType.SUMMARIZATION in max_types:
                return QueryType.SUMMARIZATION
            if QueryType.REASONING in max_types:
                return QueryType.REASONING
        
        result = max_types[0]
        logger.info(f"Query classified as: {result.value}")
        return result
    
    def get_retrieval_params(self, query_type: QueryType) -> dict:
        """Get retrieval parameters based on query type"""
        params = {
            QueryType.FACTUAL: {
                "top_k": 5,
                "use_reranker": True,
                "min_score": 0.6
            },
            QueryType.SUMMARIZATION: {
                "top_k": 10,
                "use_reranker": False,
                "min_score": 0.4
            },
            QueryType.REASONING: {
                "top_k": 8,
                "use_reranker": True,
                "min_score": 0.5
            },
            QueryType.TABLE: {
                "top_k": 6,
                "use_reranker": True,
                "min_score": 0.55
            }
        }
        
        return params.get(query_type, params[QueryType.FACTUAL])