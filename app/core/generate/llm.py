"""Gemini LLM client with conversation history support"""
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Optional
from app.config.settings import settings
from app.utils.logger import logger


class GeminiClient:
    """Client for Gemini API with conversation support"""
    
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not set")
            self.enabled = False
            return
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
        self.enabled = True
        self.conversation_history: List[Dict[str, str]] = []
        logger.info(f"Gemini client ready: {settings.LLM_MODEL}")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, context: str, query: str, has_context: bool = True, temperature: float = 0.3) -> tuple:
        """
        Generate answer based on context and conversation history.
        Returns: (answer_text, source_note)
        """
        
        if not self.enabled:
            return "LLM not configured. Please set GOOGLE_API_KEY.", None
        
        source_note = None
        
        # Build conversation context
        conversation_context = self._build_conversation_context()
        
        if has_context and context and "No relevant context" not in context:
            # Prompt with document context
            prompt = f"""You are a helpful AI assistant. Answer based on the provided context and conversation history.

CONVERSATION HISTORY:
{conversation_context}

DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer based on the document context
2. Use conversation history to understand references (e.g., "it", "this", "that")
3. Do NOT mention sources or citations in your answer
4. Just give the answer directly

ANSWER:"""
            
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 1000,
                        "top_p": 0.95,
                    }
                )
                
                answer = response.text.strip()
                source_note = self._extract_source_note(context)
                logger.info(f"Generated answer from context: {len(answer)} chars")
                
                # Store in history
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": answer})
                
                # Keep only last 10 exchanges
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return answer, source_note
                
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return f"Error: {str(e)}", None
        
        else:
            # No context - use LLM knowledge with conversation history
            prompt = f"""You are a helpful AI assistant. Answer using your general knowledge and conversation history.

CONVERSATION HISTORY:
{conversation_context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer based on your general knowledge
2. Use conversation history to understand references
3. If you don't know, say "I don't have that information in my knowledge base"

ANSWER:"""
            
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 1000,
                        "top_p": 0.95,
                    }
                )
                
                answer = response.text.strip()
                
                if any(phrase in answer.lower() for phrase in ["don't know", "not sure", "no information"]):
                    source_note = "⚠️ Not found in your documents (based on general knowledge)"
                else:
                    source_note = "ℹ️ Based on general knowledge (not from your documents)"
                
                logger.info(f"Generated answer from LLM knowledge: {len(answer)} chars")
                
                # Store in history
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": answer})
                
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return answer, source_note
                
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return f"Error: {str(e)}", None
    
    def _build_conversation_context(self) -> str:
        """Build conversation context from history"""
        if not self.conversation_history:
            return "No previous conversation."
        
        context_lines = []
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def _extract_source_note(self, context: str) -> str:
        """Extract a clean source note from context"""
        import re
        
        source_pattern = r'Document:\s*([^\n]+)'
        matches = re.findall(source_pattern, context)
        
        if matches:
            unique_sources = list(dict.fromkeys(matches))[:2]
            if len(unique_sources) == 1:
                return f"📄 From: {unique_sources[0][:40]}"
            else:
                return f"📄 From: {unique_sources[0][:30]} + {len(unique_sources)-1} more"
        
        return "📄 From your documents"