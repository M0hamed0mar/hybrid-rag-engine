"""Multi-query expansion using LLM"""
from typing import List
import google.generativeai as genai
from app.config.settings import settings
from app.utils.logger import logger


class QueryExpander:
    """Generate multiple reformulations of a query"""
    
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.LLM_MODEL)
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("LLM not available. Query expansion disabled.")
    
    def expand(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate reformulated versions of the query"""
        if not self.enabled:
            return [query]
        
        prompt = f"""Generate {num_queries} alternative reformulations of this question for better search.
Original: "{query}"

Requirements:
- Keep the same meaning
- Use different words and sentence structures
- One broader, one more specific
- Return only the queries, one per line

Reformulations:"""
        
        try:
            response = self.model.generate_content(prompt)
            expansions = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
            expansions = expansions[:num_queries]
            
            # Always include original
            all_queries = [query] + expansions
            logger.info(f"Generated {len(expansions)} query expansions")
            return all_queries
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]
    
    def expand_fallback(self, query: str) -> List[str]:
        """Simple rule-based expansion when LLM unavailable"""
        expansions = [query]
        
        # Remove question mark
        if "?" in query:
            expansions.append(query.replace("?", "."))
        
        # Extract key terms (remove common words)
        stop_words = {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an'}
        words = query.split()
        key_terms = [w for w in words if w.lower() not in stop_words]
        if key_terms and len(key_terms) < len(words):
            expansions.append(' '.join(key_terms))
        
        return list(set(expansions))[:3]