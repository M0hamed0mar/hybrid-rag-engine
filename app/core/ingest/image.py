"""Image OCR parser"""
from PIL import Image
import pytesseract
from pathlib import Path
from typing import Dict, Any
from app.config.settings import settings
from app.utils.logger import logger
from app.core.ingest.cleaner import TextCleaner


class ImageParser:
    """Extract text from images using OCR"""
    
    def __init__(self):
        self.cleaner = TextCleaner()
        
        if settings.TESSERACT_CMD != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from image"""
        logger.info(f"OCR on image: {file_path}")
        
        image = Image.open(file_path)
        
        # Convert to grayscale for better OCR
        if image.mode != 'L':
            image = image.convert('L')
        
        text = pytesseract.image_to_string(image)
        
        return {
            "text": self.cleaner.clean(text),
            "metadata": {
                "source": str(file_path),
                "document_type": "image",
                "image_size": f"{image.size[0]}x{image.size[1]}"
            }
        }