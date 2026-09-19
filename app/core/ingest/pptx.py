"""PowerPoint parser"""
from pptx import Presentation
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import logger
from app.core.ingest.cleaner import TextCleaner


class PptxParser:
    """Extract text from PowerPoint presentations"""
    
    def __init__(self):
        self.cleaner = TextCleaner()
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PPTX"""
        logger.info(f"Parsing PPTX: {file_path}")
        
        prs = Presentation(file_path)
        slides_text = []
        
        for slide in prs.slides:
            slide_content = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_content.append(self.cleaner.clean(shape.text))
            
            if slide_content:
                slides_text.append("\n".join(slide_content))
        
        return {
            "text": "\n\n".join(slides_text),
            "metadata": {
                "source": str(file_path),
                "document_type": "pptx",
                "num_slides": len(slides_text)
            }
        }