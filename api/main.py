"""
🎯 Recrut'der API - Point d'entrée principal
=============================================
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from api.config import settings
from api.routes import candidats, offres, matching, auth, entreprises, swipes, messages, notifications, cv_ai, tinder_feed, admin, support, rgpd, contact, job_ai
# from api.routes import job_boards  # Temporairement désactivé pour corriger

# Configuration du rate limiter
limiter = Limiter(key_func=get_remote_address)

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

# Middleware de sécurité pour les headers HTTP
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Headers de sécurité recommandés par OWASP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://*.supabase.co;"
        return response

# Rate limiting pour protéger contre les attaques
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Compression des réponses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware de sécurité
app.add_middleware(SecurityHeadersMiddleware)

# Trusted hosts (protection contre Host Header attacks)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list
    )

# Configuration CORS stricte pour permettre les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "Content-Range"],
    max_age=600,
)

# Inclusion des routes
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 Authentification"])
app.include_router(candidats.router, prefix="/api/candidats", tags=["👤 Candidats"])
app.include_router(offres.router, prefix="/api/offres", tags=["📋 Offres"])
app.include_router(matching.router, prefix="/api/matching", tags=["🎯 Matching IA"])

# Routes V2 - Nouvelles fonctionnalités
app.include_router(entreprises.router, prefix="/api/entreprises", tags=["🏢 Entreprises"])
app.include_router(swipes.router, prefix="/api/swipes", tags=["👍 Swipes Tinder"])
app.include_router(messages.router, prefix="/api/messages", tags=["💬 Messagerie"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["🔔 Notifications"])
app.include_router(cv_ai.router, prefix="/api/cv", tags=["🤖 IA - CV Parser"])
app.include_router(job_ai.router, prefix="/api/job", tags=["🤖 IA - Fiche de Poste Parser"])
app.include_router(tinder_feed.router, prefix="/api/tinder", tags=["🔥 Tinder Feed IA"])
app.include_router(admin.router, prefix="/api/admin", tags=["👑 Dashboard Admin"])
app.include_router(support.router, prefix="/api/support", tags=["🎫 Support & Chatbot IA"])
app.include_router(rgpd.router, prefix="/api/rgpd", tags=["🔒 RGPD & Données Personnelles"])
app.include_router(contact.router, prefix="/api/contact", tags=["📧 Contact Direct & RDV"])
# app.include_router(job_boards.router, prefix="/api/job-boards", tags=["🌐 Job Boards (Indeed, LinkedIn)"])  # Temporairement désactivé


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
