"""
🎯 Routes Matching IA
=====================
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.models.matching import MatchingResult, MatchingRequest, MatriceResponse
from api.database.fake_data import candidats_db, offres_db
from api.services.matching_engine import MatchingEngine

router = APIRouter()


@router.post("/score", response_model=MatchingResult)
async def calculer_score(request: MatchingRequest):
    if request.candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {request.candidat_id} non trouvé")
    if request.offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {request.offre_id} non trouvée")
    
    candidat = candidats_db[request.candidat_id]
    offre = offres_db[request.offre_id]
    return MatchingEngine.calculer_matching(candidat, offre)


@router.get("/candidat/{candidat_id}/top-offres")
async def top_offres_candidat(candidat_id: int, top_n: int = Query(default=5, ge=1, le=20)):
    if candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {candidat_id} non trouvé")
    
    candidat = candidats_db[candidat_id]
    offres = list(offres_db.values())
    resultats = MatchingEngine.top_offres_pour_candidat(candidat, offres, top_n)
    
    return {
        "candidat_id": candidat_id,
        "candidat_nom": candidat["nom"],
        "total_offres_analysees": len(offres),
        "matchings": resultats
    }


@router.get("/offre/{offre_id}/top-candidats")
async def top_candidats_offre(offre_id: int, top_n: int = Query(default=5, ge=1, le=20)):
    if offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {offre_id} non trouvée")
    
    offre = offres_db[offre_id]
    candidats = list(candidats_db.values())
    resultats = MatchingEngine.top_candidats_pour_offre(offre, candidats, top_n)
    
    return {
        "offre_id": offre_id,
        "offre_titre": offre["titre"],
        "entreprise": offre["entreprise"],
        "total_candidats_analyses": len(candidats),
        "matchings": resultats
    }


@router.get("/matrice", response_model=MatriceResponse)
async def matrice_complete():
    candidats = list(candidats_db.values())
    offres = list(offres_db.values())
    return MatchingEngine.matrice_complete(candidats, offres)


@router.get("/statistiques")
async def statistiques_matching():
    candidats = list(candidats_db.values())
    offres = list(offres_db.values())
    matrice = MatchingEngine.matrice_complete(candidats, offres)
    
    matchings_tries = sorted(matrice["matchings"], key=lambda x: x["score"], reverse=True)
    
    return {
        "total_candidats": len(candidats),
        "total_offres": len(offres),
        "statistiques": matrice["statistiques"],
        "meilleur_match": matchings_tries[0] if matchings_tries else None,
        "top_5_matchs": matchings_tries[:5],
        "poids_utilises": MatchingEngine.POIDS
    }
