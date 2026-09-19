"""Context construction from retrieved chunks"""
from typing import List, Tuple
import tiktoken
from app.config.settings import settings
from app.utils.logger import logger
from app.core.chunk.models import DocumentChunk


class ContextBuilder:
    """Build structured context from top-K chunks"""
    
    def __init__(self):
        self.max_tokens = settings.MAX_CONTEXT_TOKENS
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def build_context(
        self,
        chunks: List[Tuple[DocumentChunk, float]],
        include_metadata: bool = True
    ) -> str:
        """Build context from ranked chunks"""
        
        if not chunks:
            return "No relevant context found."
        
        context_parts = ["=== DOCUMENT CONTEXT ===\n"]
        total_tokens = self.count_tokens(context_parts[0])
        
        for i, (chunk, score) in enumerate(chunks, 1):
            # Header with source
            header = f"\n[Source {i}] (relevance: {score:.3f})"
            if include_metadata:
                header += f"\nDocument: {chunk.source}"
                if chunk.section_title:
                    header += f"\nSection: {chunk.section_title}"
                if chunk.page_number:
                    header += f"\nPage: {chunk.page_number}"
            
            header_tokens = self.count_tokens(header)
            content = chunk.text_with_context
            content_tokens = self.count_tokens(content)
            
            # Check token limit
            if total_tokens + header_tokens + content_tokens > self.max_tokens:
                remaining = self.max_tokens - total_tokens - header_tokens - 50
                if remaining > 100:
                    # Truncate content
                    tokens = self.tokenizer.encode(content)
                    truncated = self.tokenizer.decode(tokens[:remaining])
                    content = truncated + "\n[truncated]"
                else:
                    break
            
            context_parts.append(header)
            context_parts.append(content)
            total_tokens += header_tokens + self.count_tokens(content)
        
        # Add instructions
        context_parts.append("\n=== INSTRUCTIONS ===")
        context_parts.append("Answer based ONLY on the above context.")
        context_parts.append("If the answer isn't in the context, say so clearly.")
        context_parts.append("Cite sources using [Source X] notation.")
        
        context = "\n".join(context_parts)
        logger.info(f"Built context: {len(chunks)} chunks, {self.count_tokens(context)} tokens")
        
        return context