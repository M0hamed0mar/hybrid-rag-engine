"""Semantic chunking with section awareness"""
from typing import List, Optional
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config.settings import settings
from app.utils.logger import logger
from app.core.chunk.models import DocumentChunk


class SemanticChunker:
    """Context-aware document chunking"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        
        # Heading detection patterns
        self.heading_patterns = [
            r'^#{1,6}\s+(.+)$',           # Markdown headings
            r'^([A-Z][A-Z\s]{5,})$',      # ALL CAPS headings
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$',  # Title Case
            r'^\d+\.\s+(.+)$',             # Numbered sections
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:$',   # Heading with colon
        ]
    
    def _extract_section_title(self, text: str) -> Optional[str]:
        """Extract section title from text beginning"""
        lines = text.strip().split('\n')[:3]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) > 100:  # Title shouldn't be too long
                continue
            
            for pattern in self.heading_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    title = match.group(1) if match.groups() else line
                    return title[:100]  # Limit title length
        
        return None
    
    def chunk_document(
        self,
        text: str,
        source: str,
        document_type: str
    ) -> List[DocumentChunk]:
        """Split document into semantic chunks"""
        logger.info(f"Chunking document: {source}")
        
        if not text or not text.strip():
            logger.warning(f"Empty document: {source}")
            return []
        
        # Split text
        raw_chunks = self.text_splitter.split_text(text)
        
        chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue
            
            chunk = DocumentChunk(
                content=chunk_text,
                section_title=self._extract_section_title(chunk_text),
                source=source,
                document_type=document_type,
                chunk_index=idx,
                metadata={
                    "chunk_size": len(chunk_text),
                    "has_heading": self._extract_section_title(chunk_text) is not None
                }
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from {source}")
        return chunks