"""
🔐 Recrut'der - Service Supabase
=================================
Gestion de la connexion et des opérations Supabase
"""

from supabase import create_client, Client
from api.config import settings
from loguru import logger

class SupabaseService:
    """Service singleton pour gérer la connexion Supabase"""
    
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Retourne l'instance Supabase (singleton)"""
        if cls._instance is None:
            try:
                cls._instance = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_KEY
                )
                logger.info("✅ Connexion Supabase établie")
            except Exception as e:
                logger.error(f"❌ Erreur connexion Supabase: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """Retourne un client avec les droits admin (service_role)"""
        if not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY non configurée")
        
        return create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY
        )


# Instance globale
supabase: Client = SupabaseService.get_client()
