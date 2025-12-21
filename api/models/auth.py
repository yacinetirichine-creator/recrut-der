"""
🔐 Recrut'der - Modèles d'authentification
==========================================
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from enum import Enum


class TypeUtilisateur(str, Enum):
    """Type d'utilisateur"""
    CANDIDAT = "candidat"
    RECRUTEUR = "recruteur"


class UserRegister(BaseModel):
    """Modèle pour l'inscription"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    type_utilisateur: TypeUtilisateur
    telephone: Optional[str] = None
    
    # Champs spécifiques recruteur
    entreprise: Optional[str] = None
    poste: Optional[str] = None
    
    @validator('password')
    def password_complexity(cls, v):
        """Validation basique du mot de passe"""
        if len(v) < 6:
            raise ValueError('Le mot de passe doit contenir au moins 6 caractères')
        return v
    
    @validator('entreprise')
    def entreprise_required_for_recruteur(cls, v, values):
        """L'entreprise est obligatoire pour les recruteurs"""
        if values.get('type_utilisateur') == TypeUtilisateur.RECRUTEUR and not v:
            raise ValueError("Le nom de l'entreprise est obligatoire pour les recruteurs")
        return v


class UserLogin(BaseModel):
    """Modèle pour la connexion"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Modèle de réponse JWT"""
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_in: int


class UserResponse(BaseModel):
    """Modèle de réponse utilisateur"""
    id: str
    email: str
    nom: str
    prenom: Optional[str]
    type_utilisateur: TypeUtilisateur
    telephone: Optional[str]
    photo_url: Optional[str]
    bio: Optional[str]
    linkedin_url: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Modèle pour réinitialisation mot de passe"""
    email: EmailStr


class PasswordUpdate(BaseModel):
    """Modèle pour mise à jour mot de passe"""
    current_password: str
    new_password: str = Field(..., min_length=6)
    
    @validator('new_password')
    def password_complexity(cls, v):
        if len(v) < 6:
            raise ValueError('Le mot de passe doit contenir au moins 6 caractères')
        return v


class UserUpdate(BaseModel):
    """Modèle pour mise à jour profil utilisateur"""
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    telephone: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
