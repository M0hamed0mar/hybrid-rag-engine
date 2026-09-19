"""Application configuration management"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings"""
    
    # ========== API Keys ==========
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # ========== OCR Settings ==========
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # ========== Chunking Settings ==========
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # ========== Retrieval Settings ==========
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "10"))
    TOP_K_RERANK: int = int(os.getenv("TOP_K_RERANK", "5"))
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    
    # ========== Model Settings ==========
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL: str = "models/gemini-2.5-flash"
    
    # ========== Server Settings ==========
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # ========== Paths ==========
    DATA_DIR: Path = DATA_DIR
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHROMA_DIR: Path = DATA_DIR / "chroma"
    CACHE_DIR: Path = DATA_DIR / "cache"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
        self._validate_config()
    
    def _create_directories(self):
        """Create necessary directories"""
        for dir_path in [self.UPLOAD_DIR, self.CHROMA_DIR, self.CACHE_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Validate configuration"""
        if not self.GOOGLE_API_KEY:
            print("⚠️  WARNING: GOOGLE_API_KEY not set. LLM features disabled.")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()