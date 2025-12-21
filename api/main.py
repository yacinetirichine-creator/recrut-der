"""
🎯 Recrut'der API - Point d'entrée principal
=============================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.config import settings
from api.routes import candidats, offres, matching, auth

# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🎯 Recrut'der - Le Tinder du Recrutement

API de matching IA entre candidats et offres d'emploi.

### Fonctionnalités

* **Candidats** - Gérer les profils candidats
* **Offres** - Gérer les offres d'emploi  
* **Matching IA** - Algorithme intelligent de scoring multi-critères

### Critères de Matching

| Critère | Poids |
|---------|-------|
| Compétences techniques | 25% |
| Expérience | 25% |
| Qualifications | 25% |
| Salaire | 8% |
| Localisation | 7% |
| Autres | 10% |
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS pour permettre les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 Authentification"])
app.include_router(candidats.router, prefix="/api/candidats", tags=["👤 Candidats"])
app.include_router(offres.router, prefix="/api/offres", tags=["📋 Offres"])
app.include_router(matching.router, prefix="/api/matching", tags=["🎯 Matching IA"])


# Route racine
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🎯 Bienvenue sur Recrut'der API",
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "endpoints": {
            "candidats": "/api/candidats",
            "offres": "/api/offres",
            "matching": "/api/matching"
        }
    }


# Health check
@app.get("/health", tags=["Root"])
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Recrut'der API démarrée")
    logger.info(f"📚 Documentation: http://localhost:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Recrut'der API arrêtée")
