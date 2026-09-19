#!/usr/bin/env python3
"""Development server runner"""
import uvicorn
from app.config.settings import settings
import socket


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


if __name__ == "__main__":
    port = settings.PORT
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print("🎯 RAG System - Ready to use!")
    print("=" * 60)
    print(f"\n📱 Open in your browser:")
    print(f"   \x1b]8;;http://localhost:{port}\x1b\\http://localhost:{port}\x1b]8;;\x1b\\")
    print(f"   \x1b]8;;http://127.0.0.1:{port}\x1b\\http://127.0.0.1:{port}\x1b]8;;\x1b\\")
    if local_ip != "127.0.0.1":
        print(f"   \x1b]8;;http://{local_ip}:{port}\x1b\\http://{local_ip}:{port}\x1b]8;;\x1b\\")
    print("\n" + "=" * 60)
    print("💡 Tip: Ctrl+Click on the link above to open directly")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )