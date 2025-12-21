"""
📋 Modèle Offre d'emploi
========================
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TypeContratEnum(str, Enum):
    CDI = "cdi"
    CDD = "cdd"
    FREELANCE = "freelance"
    STAGE = "stage"
    ALTERNANCE = "alternance"


class TeletravailEnum(str, Enum):
    FULL_REMOTE = "full_remote"
    HYBRIDE = "hybride"
    PRESENTIEL = "presentiel"


class DateDebutEnum(str, Enum):
    IMMEDIATE = "immediate"
    UN_MOIS = "1_mois"
    TROIS_MOIS = "3_mois"
    FLEXIBLE = "flexible"


class OffreBase(BaseModel):
    titre: str = Field(..., min_length=5, max_length=200)
    entreprise: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    
    competences_requises: List[str] = Field(default=[])
    competences_bonus: List[str] = Field(default=[])
    soft_skills_recherches: List[str] = Field(default=[])
    
    experience_min: int = Field(..., ge=0)
    experience_max: int = Field(..., ge=0)
    
    qualifications_requises: List[str] = Field(default=[])
    qualifications_bonus: List[str] = Field(default=[])
    niveau_etudes_min: str = Field(default="bac+3")
    
    salaire_min: int = Field(..., ge=0)
    salaire_max: int = Field(..., ge=0)
    
    localisation: str
    remote_possible: bool = Field(default=False)
    politique_teletravail: TeletravailEnum = Field(default=TeletravailEnum.HYBRIDE)
    
    secteur: str
    type_contrat: TypeContratEnum = Field(default=TypeContratEnum.CDI)
    date_debut_souhaitee: DateDebutEnum = Field(default=DateDebutEnum.UN_MOIS)
    
    langues_requises: List[str] = Field(default=["français"])
    langues_bonus: List[str] = Field(default=[])
    
    taille_entreprise: str = Field(default="pme")


class OffreCreate(OffreBase):
    pass


class OffreUpdate(BaseModel):
    titre: Optional[str] = None
    entreprise: Optional[str] = None
    description: Optional[str] = None
    competences_requises: Optional[List[str]] = None
    competences_bonus: Optional[List[str]] = None
    soft_skills_recherches: Optional[List[str]] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    qualifications_requises: Optional[List[str]] = None
    qualifications_bonus: Optional[List[str]] = None
    niveau_etudes_min: Optional[str] = None
    salaire_min: Optional[int] = None
    salaire_max: Optional[int] = None
    localisation: Optional[str] = None
    remote_possible: Optional[bool] = None
    politique_teletravail: Optional[TeletravailEnum] = None
    secteur: Optional[str] = None
    type_contrat: Optional[TypeContratEnum] = None
    date_debut_souhaitee: Optional[DateDebutEnum] = None
    langues_requises: Optional[List[str]] = None
    langues_bonus: Optional[List[str]] = None
    taille_entreprise: Optional[str] = None


class Offre(OffreBase):
    id: int
    
    class Config:
        from_attributes = True
