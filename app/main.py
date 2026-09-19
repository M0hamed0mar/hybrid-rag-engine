"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
from app.api.routes import router
from app.utils.logger import logger
from app.config.settings import settings
import socket


# Get the project root directory
BASE_DIR = Path(__file__).parent.parent
WEB_DIR = BASE_DIR / "web"


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    from app.core.pipeline import RAGPipeline
    pipeline = RAGPipeline()
    
    # Get local IP and port
    local_ip = get_local_ip()
    port = settings.PORT
    
    logger.info("=" * 60)
    logger.info("🚀 RAG System started successfully!")
    logger.info("=" * 60)
    logger.info(f"📚 Total chunks: {pipeline.vector_store.get_count()}")
    logger.info(f"🤖 LLM: {'Enabled' if pipeline.llm.enabled else 'Disabled'}")
    logger.info("")
    logger.info("📍 Access the application at:")
    logger.info(f"   ➜ Local:   http://localhost:{port}")
    logger.info(f"   ➜ Local:   http://127.0.0.1:{port}")
    if local_ip != "127.0.0.1":
        logger.info(f"   ➜ Network: http://{local_ip}:{port}")
    logger.info("")
    logger.info("📚 API Documentation:")
    logger.info(f"   ➜ Swagger UI: http://localhost:{port}/docs")
    logger.info(f"   ➜ ReDoc:      http://localhost:{port}/redoc")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down RAG System...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="RAG System",
    description="Intelligent Document Assistant",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Serve static files (HTML, CSS, JS)
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "RAG System is running. Please access /docs for API documentation."}


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "service": "RAG System"}