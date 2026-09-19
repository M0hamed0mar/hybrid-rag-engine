"""Word document parser"""
import docx
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import logger
from app.core.ingest.cleaner import TextCleaner


class DocxParser:
    """Extract text from Word documents"""
    
    def __init__(self):
        self.cleaner = TextCleaner()
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from DOCX"""
        logger.info(f"Parsing DOCX: {file_path}")
        
        doc = docx.Document(file_path)
        paragraphs = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(self.cleaner.clean(para.text))
        
        return {
            "text": "\n\n".join(paragraphs),
            "metadata": {
                "source": str(file_path),
                "document_type": "docx",
                "num_paragraphs": len(paragraphs)
            }
        }