"""
🚀 Recrut'der - Script de démarrage
===================================
Lance l'API FastAPI avec uvicorn
"""

import uvicorn
from api.config import settings

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🎯 RECRUT'DER API v2.0                                     ║
    ║   Le Tinder du recrutement - Matching IA                     ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║   📡 API:          http://localhost:8000                     ║
    ║   📚 Swagger:      http://localhost:8000/docs                ║
    ║   📖 ReDoc:        http://localhost:8000/redoc               ║
    ║                                                               ║
    ║   Appuyez sur CTRL+C pour arrêter le serveur                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
