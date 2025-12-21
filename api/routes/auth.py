"""
🔐 Recrut'der - Routes d'authentification
=========================================
Endpoints pour inscription, connexion, déconnexion
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from api.models.auth import (
    UserRegister, 
    UserLogin, 
    Token, 
    UserResponse,
    PasswordReset,
    UserUpdate
)
from api.services.auth_service import AuthService
from loguru import logger


router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dépendance pour récupérer l'utilisateur connecté"""
    return await AuthService.get_current_user(credentials.credentials)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    📝 Inscription d'un nouveau compte
    
    - **email**: Email unique
    - **password**: Mot de passe (min 6 caractères)
    - **nom**: Nom complet
    - **type_utilisateur**: "candidat" ou "recruteur"
    - **entreprise**: Obligatoire si recruteur
    """
    logger.info(f"📝 Tentative d'inscription: {user_data.email} ({user_data.type_utilisateur.value})")
    return await AuthService.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    🔐 Connexion
    
    Retourne un token JWT à utiliser dans le header Authorization
    """
    logger.info(f"🔐 Tentative de connexion: {credentials.email}")
    return await AuthService.login_user(credentials)


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    👋 Déconnexion
    
    Invalide le token actuel
    """
    await AuthService.logout_user(credentials.credentials)
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=Dict[str, Any])
async def get_profile(current_user: Dict = Depends(get_current_user)):
    """
    👤 Profil de l'utilisateur connecté
    
    Retourne les informations complètes de l'utilisateur
    """
    return current_user


@router.post("/reset-password")
async def request_password_reset(data: PasswordReset):
    """
    🔑 Demander une réinitialisation de mot de passe
    
    Envoie un email avec un lien de réinitialisation
    """
    await AuthService.reset_password(data.email)
    return {
        "message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé"
    }


@router.get("/verify-token")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    ✅ Vérifier si le token est valide
    
    Utile pour le frontend pour vérifier l'authentification
    """
    return {
        "valid": True,
        "user_id": current_user["id"],
        "type_utilisateur": current_user["type_utilisateur"]
    }
