"""
🎯 Modèle Matching
==================
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class NiveauMatchEnum(str, Enum):
    EXCELLENT = "excellent"
    TRES_BON = "tres_bon"
    CORRECT = "correct"
    FAIBLE = "faible"
    INCOMPATIBLE = "incompatible"


class ScoreDetail(BaseModel):
    score: float = Field(..., ge=0, le=100)
    detail: str
    requises_manquantes: Optional[List[str]] = None
    bonus_trouvees: Optional[List[str]] = None


class MatchingResult(BaseModel):
    candidat_id: int
    offre_id: int
    candidat_nom: str
    offre_titre: str
    entreprise: str
    
    score_global: float = Field(..., ge=0, le=100)
    niveau: NiveauMatchEnum
    emoji: str
    recommandation: str
    
    scores_details: Dict[str, ScoreDetail]
    points_forts: List[str] = Field(default=[])
    points_faibles: List[str] = Field(default=[])
    
    class Config:
        from_attributes = True


class MatchingRequest(BaseModel):
    candidat_id: int
    offre_id: int


class MatriceEntry(BaseModel):
    candidat_id: int
    candidat_nom: str
    offre_id: int
    offre_titre: str
    score: float
    niveau: NiveauMatchEnum
    emoji: str


class MatriceResponse(BaseModel):
    total_candidats: int
    total_offres: int
    total_matchings: int
    matchings: List[MatriceEntry]
    statistiques: Dict[str, Any]
