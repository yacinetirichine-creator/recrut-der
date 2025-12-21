"""
📋 Modèle Offre d'emploi
========================
Support multilingue et parsing automatique par IA
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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


class StatutOffreEnum(str, Enum):
    BROUILLON = "brouillon"
    PUBLIEE = "publiee"
    ARCHIVEE = "archivee"
    EXPIREE = "expiree"


class OffreBase(BaseModel):
    titre: str = Field(..., min_length=5, max_length=200)
    entreprise: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    description_courte: Optional[str] = Field(None, max_length=500, description="Résumé court de l'offre")
    
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
    ville: Optional[str] = None
    pays: Optional[str] = Field(default="France")
    code_postal: Optional[str] = None
    remote_possible: bool = Field(default=False)
    politique_teletravail: TeletravailEnum = Field(default=TeletravailEnum.HYBRIDE)
    
    secteur: str
    type_contrat: TypeContratEnum = Field(default=TypeContratEnum.CDI)
    date_debut_souhaitee: DateDebutEnum = Field(default=DateDebutEnum.UN_MOIS)
    
    langues_requises: List[str] = Field(default=["français"])
    langues_bonus: List[str] = Field(default=[])
    
    taille_entreprise: str = Field(default="pme")
    
    # Nouveaux champs pour support multilingue et parsing IA
    avantages: List[str] = Field(default=[], description="Avantages de l'offre (tickets restaurant, mutuelle, etc.)")
    responsabilites: List[str] = Field(default=[], description="Responsabilités du poste")
    missions_principales: List[str] = Field(default=[], description="Missions principales")
    langue: str = Field(default="fr", description="Langue de l'offre (en, fr, es, de, zh, hi, ar, bn, ru, pt)")
    statut: StatutOffreEnum = Field(default=StatutOffreEnum.BROUILLON, description="Statut de l'offre")
    source_parsing: Optional[str] = Field(None, description="Source du parsing (manual, ai_pdf, ai_text)")
    parsed_metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées du parsing IA")

class OffreCreate(OffreBase):
    """Modèle pour créer une nouvelle offre"""
    pass


class OffreUpdate(BaseModel):
    """Modèle pour mettre à jour une offre existante"""
    titre: Optional[str] = None
    entreprise: Optional[str] = None
    description: Optional[str] = None
    description_courte: Optional[str] = None
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
    ville: Optional[str] = None
    pays: Optional[str] = None
    code_postal: Optional[str] = None
    remote_possible: Optional[bool] = None
    politique_teletravail: Optional[TeletravailEnum] = None
    secteur: Optional[str] = None
    type_contrat: Optional[TypeContratEnum] = None
    date_debut_souhaitee: Optional[DateDebutEnum] = None
    langues_requises: Optional[List[str]] = None
    langues_bonus: Optional[List[str]] = None
    taille_entreprise: Optional[str] = None
    avantages: Optional[List[str]] = None
    responsabilites: Optional[List[str]] = None
    missions_principales: Optional[List[str]] = None
    langue: Optional[str] = None
    statut: Optional[StatutOffreEnum] = None
    source_parsing: Optional[str] = None
    parsed_metadata: Optional[Dict[str, Any]] = None


class Offre(OffreBase):
    """Modèle complet d'une offre avec ID"""
    id: int
    
    class Config:
        from_attributes = True


class OffreParsed(BaseModel):
    """Modèle pour les données d'une offre parsée par IA (avant validation)"""
    titre_poste: str
    entreprise: Optional[str] = None
    description_complete: str
    description_courte: str
    competences_requises: List[str] = Field(default=[])
    competences_bonus: List[str] = Field(default=[])
    soft_skills_recherches: List[str] = Field(default=[])
    experience_min: int = 0
    experience_max: int = 0
    qualifications_requises: List[str] = Field(default=[])
    qualifications_bonus: List[str] = Field(default=[])
    niveau_etudes_min: str = "bac+3"
    salaire_min: int = 0
    salaire_max: int = 0
    salaire_devise: str = "EUR"
    salaire_periode: str = "annuel"
    localisation: str
    ville: Optional[str] = None
    pays: str = "France"
    code_postal: Optional[str] = None
    remote_possible: bool = False
    politique_teletravail: str = "hybride"
    secteur: str
    type_contrat: str = "cdi"
    date_debut_souhaitee: str = "1_mois"
    langues_requises: List[str] = Field(default=["français"])
    langues_bonus: List[str] = Field(default=[])
    taille_entreprise: str = "pme"
    avantages: List[str] = Field(default=[])
    responsabilites: List[str] = Field(default=[])
    missions_principales: List[str] = Field(default=[])
    langue_source: Optional[str] = None
    langue_cible: Optional[str] = None
    fichier_original: Optional[str] = None
    recruteur_id: Optional[int] = None
    
    class Config:
        from_attributes = True
