"""
⚙️ Recrut'der - Configuration
==============================
Gestion des variables d'environnement et paramètres
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Général
    APP_NAME: str = "Recrut'der API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # anon key
    SUPABASE_SERVICE_KEY: Optional[str] = None  # service_role key (admin)
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - Origines autorisées pour le frontend
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    
    # Trusted Hosts (pour production)
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    # IA - API Keys pour parsing CV et chatbot
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit la string CORS_ORIGINS en liste"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convertit la string ALLOWED_HOSTS en liste"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instance globale
settings = Settings()
