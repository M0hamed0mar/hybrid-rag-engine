"""Chunk data models"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import uuid4


@dataclass
class DocumentChunk:
    """Represents a semantic chunk of a document"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    source: str = ""
    document_type: str = ""
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "section_title": self.section_title,
            "page_number": self.page_number,
            "source": self.source,
            "document_type": self.document_type,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid4())),
            content=data.get("content", ""),
            section_title=data.get("section_title"),
            page_number=data.get("page_number"),
            source=data.get("source", ""),
            document_type=data.get("document_type", ""),
            chunk_index=data.get("chunk_index", 0),
            metadata=data.get("metadata", {})
        )
    
    @property
    def text_with_context(self) -> str:
        """Get text with optional section title"""
        if self.section_title:
            return f"## {self.section_title}\n\n{self.content}"
        return self.content