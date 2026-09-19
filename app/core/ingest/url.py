"""Web URL parser"""
import trafilatura
from typing import Dict, Any
from app.utils.logger import logger
from app.core.ingest.cleaner import TextCleaner


class URLParser:
    """Extract content from web URLs"""
    
    def __init__(self):
        self.cleaner = TextCleaner()
    
    def parse(self, url: str) -> Dict[str, Any]:
        """Extract content from URL"""
        logger.info(f"Parsing URL: {url}")
        
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            raise ValueError(f"Failed to fetch URL: {url}")
        
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True
        )
        
        if not text:
            raise ValueError(f"No extractable content from: {url}")
        
        metadata = trafilatura.extract_metadata(downloaded)
        
        return {
            "text": self.cleaner.clean(text),
            "metadata": {
                "source": url,
                "document_type": "url",
                "title": metadata.title if metadata else None,
                "author": metadata.author if metadata else None
            }
        }