"""Main document loader dispatcher"""
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logger import logger
from app.core.ingest.pdf import PDFParser
from app.core.ingest.docx import DocxParser
from app.core.ingest.pptx import PptxParser
from app.core.ingest.image import ImageParser
from app.core.ingest.url import URLParser


class DocumentLoader:
    """Unified document loader for all formats"""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.docx_parser = DocxParser()
        self.pptx_parser = PptxParser()
        self.image_parser = ImageParser()
        self.url_parser = URLParser()
    
    def load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load document from file path"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self.pdf_parser.parse(file_path)
        elif suffix == '.docx':
            return self.docx_parser.parse(file_path)
        elif suffix == '.pptx':
            return self.pptx_parser.parse(file_path)
        elif suffix in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.image_parser.parse(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def load_url(self, url: str) -> Dict[str, Any]:
        """Load document from URL"""
        return self.url_parser.parse(url)
    
    def load_text(self, text: str, source: str = "direct_input") -> Dict[str, Any]:
        """Load direct text input"""
        from app.core.ingest.cleaner import TextCleaner
        cleaner = TextCleaner()
        
        return {
            "text": cleaner.clean(text),
            "metadata": {
                "source": source,
                "document_type": "text"
            }
        }
    