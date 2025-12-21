"""
🔐 Recrut'der - Service d'authentification
==========================================
Gestion complète de l'authentification avec Supabase
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import JWTError, jwt
from loguru import logger

from api.config import settings
from api.database.supabase_client import supabase
from api.models.auth import UserRegister, UserLogin, Token, TypeUtilisateur


class AuthService:
    """Service d'authentification"""
    
    @staticmethod
    async def register_user(user_data: UserRegister) -> Token:
        """
        Inscription d'un nouvel utilisateur (candidat ou recruteur)
        """
        try:
            # 1. Créer l'utilisateur dans Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "nom": user_data.nom,
                        "prenom": user_data.prenom,
                        "type_utilisateur": user_data.type_utilisateur.value,
                        "telephone": user_data.telephone
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erreur lors de la création du compte"
                )
            
            user_id = auth_response.user.id
            
            # 2. Créer le profil spécifique selon le type
            if user_data.type_utilisateur == TypeUtilisateur.CANDIDAT:
                # Créer un profil candidat vide
                supabase.table("candidats").insert({
                    "user_id": user_id,
                    "salaire_min": 0,
                    "salaire_max": 0,
                    "localisation": "à définir",
                    "actif": False  # Inactif tant que le profil n'est pas complété
                }).execute()
                logger.info(f"✅ Profil candidat créé pour {user_data.email}")
                
            elif user_data.type_utilisateur == TypeUtilisateur.RECRUTEUR:
                # Créer un profil recruteur
                recruteur_data = {
                    "user_id": user_id,
                    "entreprise": user_data.entreprise,
                    "poste": user_data.poste,
                    "actif": True
                }
                supabase.table("recruteurs").insert(recruteur_data).execute()
                logger.info(f"✅ Profil recruteur créé pour {user_data.email} ({user_data.entreprise})")
            
            # 3. Retourner le token
            return Token(
                access_token=auth_response.session.access_token,
                token_type="bearer",
                user={
                    "id": user_id,
                    "email": user_data.email,
                    "nom": user_data.nom,
                    "prenom": user_data.prenom,
                    "type_utilisateur": user_data.type_utilisateur.value
                },
                expires_in=auth_response.session.expires_in
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur inscription: {e}")
            if "User already registered" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Un compte existe déjà avec cet email"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de l'inscription: {str(e)}"
            )
    
    @staticmethod
    async def login_user(credentials: UserLogin) -> Token:
        """
        Connexion d'un utilisateur
        """
        try:
            # Authentification avec Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect"
                )
            
            user_id = auth_response.user.id
            
            # Récupérer les infos utilisateur
            user_info = supabase.table("utilisateurs").select("*").eq("id", user_id).single().execute()
            
            if not user_info.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé"
                )
            
            return Token(
                access_token=auth_response.session.access_token,
                token_type="bearer",
                user={
                    "id": user_id,
                    "email": user_info.data["email"],
                    "nom": user_info.data["nom"],
                    "prenom": user_info.data.get("prenom"),
                    "type_utilisateur": user_info.data["type_utilisateur"]
                },
                expires_in=auth_response.session.expires_in
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erreur connexion: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
    
    @staticmethod
    async def logout_user(token: str):
        """
        Déconnexion d'un utilisateur
        """
        try:
            supabase.auth.sign_out()
            logger.info("✅ Déconnexion réussie")
        except Exception as e:
            logger.error(f"❌ Erreur déconnexion: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la déconnexion"
            )
    
    @staticmethod
    async def get_current_user(token: str) -> Dict[str, Any]:
        """
        Récupérer l'utilisateur depuis le token JWT
        """
        try:
            # Vérifier le token avec Supabase
            user = supabase.auth.get_user(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide ou expiré"
                )
            
            # Récupérer les infos complètes
            user_info = supabase.table("utilisateurs").select("*").eq("id", user.user.id).single().execute()
            
            return user_info.data
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération utilisateur: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Non authentifié"
            )
    
    @staticmethod
    async def reset_password(email: str):
        """
        Demander une réinitialisation de mot de passe
        """
        try:
            supabase.auth.reset_password_for_email(email)
            logger.info(f"✅ Email de réinitialisation envoyé à {email}")
        except Exception as e:
            logger.error(f"❌ Erreur réinitialisation: {e}")
            # Ne pas révéler si l'email existe ou non
            pass
