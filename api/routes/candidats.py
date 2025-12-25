"""
👤 Routes Candidats
===================
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any

from api.models.candidat import Candidat, CandidatCreate, CandidatUpdate
from api.database.fake_data import candidats_db, get_next_candidat_id
from api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[Candidat])
async def lister_candidats(current_user: Dict[str, Any] = Depends(get_current_user)):
    return list(candidats_db.values())


@router.get("/{candidat_id}", response_model=Candidat)
async def get_candidat(candidat_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    if candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {candidat_id} non trouvé")
    return candidats_db[candidat_id]


@router.post("/", response_model=Candidat, status_code=201)
async def creer_candidat(candidat: CandidatCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    new_id = get_next_candidat_id()
    candidat_data = candidat.model_dump()
    candidat_data["id"] = new_id
    
    for key, value in candidat_data.items():
        if hasattr(value, "value"):
            candidat_data[key] = value.value
    
    candidats_db[new_id] = candidat_data
    return candidat_data


@router.put("/{candidat_id}", response_model=Candidat)
async def modifier_candidat(candidat_id: int, candidat_update: CandidatUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    if candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {candidat_id} non trouvé")
    
    candidat_actuel = candidats_db[candidat_id]
    update_data = candidat_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if hasattr(value, "value"):
            update_data[key] = value.value
    
    candidat_actuel.update(update_data)
    candidats_db[candidat_id] = candidat_actuel
    return candidat_actuel


@router.delete("/{candidat_id}", status_code=204)
async def supprimer_candidat(candidat_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    if candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {candidat_id} non trouvé")
    del candidats_db[candidat_id]
    return None
