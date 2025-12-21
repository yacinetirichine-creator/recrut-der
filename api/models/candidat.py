"""
👤 Modèle Candidat
==================
Définition du schéma de données pour les candidats
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DisponibiliteEnum(str, Enum):
    IMMEDIATE = "immediate"
    UN_MOIS = "1_mois"
    TROIS_MOIS = "3_mois"


class TeletravailEnum(str, Enum):
    FULL_REMOTE = "full_remote"
    HYBRIDE = "hybride"
    PRESENTIEL = "presentiel"


class CandidatBase(BaseModel):
    """Champs communs pour Candidat"""
    nom: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = None
    
    competences_techniques: List[str] = Field(default=[])
    soft_skills: List[str] = Field(default=[])
    
    experience_annees: int = Field(..., ge=0, le=50)
    
    qualifications: List[str] = Field(default=[])
    niveau_etudes: str = Field(default="bac+3")
    
    salaire_min: int = Field(..., ge=0)
    salaire_max: int = Field(..., ge=0)
    
    localisation: str
    accept_remote: bool = Field(default=False)
    preference_teletravail: TeletravailEnum = Field(default=TeletravailEnum.HYBRIDE)
    
    secteurs: List[str] = Field(default=[])
    type_contrat_souhaite: List[str] = Field(default=["cdi"])
    disponibilite: DisponibiliteEnum = Field(default=DisponibiliteEnum.UN_MOIS)
    langues: List[str] = Field(default=["français"])
    taille_entreprise_preferee: List[str] = Field(default=[])


class CandidatCreate(CandidatBase):
    pass


class CandidatUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[str] = None
    competences_techniques: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    experience_annees: Optional[int] = None
    qualifications: Optional[List[str]] = None
    niveau_etudes: Optional[str] = None
    salaire_min: Optional[int] = None
    salaire_max: Optional[int] = None
    localisation: Optional[str] = None
    accept_remote: Optional[bool] = None
    preference_teletravail: Optional[TeletravailEnum] = None
    secteurs: Optional[List[str]] = None
    type_contrat_souhaite: Optional[List[str]] = None
    disponibilite: Optional[DisponibiliteEnum] = None
    langues: Optional[List[str]] = None
    taille_entreprise_preferee: Optional[List[str]] = None


class Candidat(CandidatBase):
    id: int
    
    class Config:
        from_attributes = True
