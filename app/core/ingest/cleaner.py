"""Text cleaning and normalization"""
import re
from typing import List, Dict, Any


class TextCleaner:
    """Clean and normalize extracted text"""
    
    @staticmethod
    def clean(text: str) -> str:
        """Apply all cleaning operations"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Fix common OCR issues
        text = text.replace('|', 'I')
        
        return text.strip()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize all whitespace to single spaces"""
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def extract_tables(text: str) -> List[Dict]:
        """Extract table-like structures"""
        tables = []
        
        # Markdown table pattern
        md_pattern = r'(\|[\s\w]+\|[\s\w]+\|(?:\n\|[-:\s|]+\|)?(?:\n\|[\s\w|]+\|)+)'
        md_tables = re.findall(md_pattern, text, re.MULTILINE)
        
        for table in md_tables:
            tables.append({"type": "markdown", "content": table})
        
        # ASCII table pattern
        ascii_pattern = r'(\+[-+]+\+\n(?:\|.+\|\n\+[-+]+\+\n?)+)'
        ascii_tables = re.findall(ascii_pattern, text)
        
        for table in ascii_tables:
            tables.append({"type": "ascii", "content": table})
        
        return tables