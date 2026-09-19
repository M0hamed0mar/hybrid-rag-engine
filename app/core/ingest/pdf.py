"""PDF document parser"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import logger
from app.core.ingest.cleaner import TextCleaner


class PDFParser:
    """Extract text from PDF files"""
    
    def __init__(self):
        self.cleaner = TextCleaner()
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF"""
        logger.info(f"Parsing PDF: {file_path}")
        
        doc = fitz.open(file_path)
        all_text = []
        pages = []
        
        for page_num, page in enumerate(doc, start=1):
            text = self.cleaner.clean(page.get_text())
            pages.append({"page": page_num, "text": text})
            all_text.append(text)
        
        doc.close()
        
        return {
            "text": "\n\n".join(all_text),
            "metadata": {
                "source": str(file_path),
                "document_type": "pdf",
                "num_pages": len(pages)
            }
        }