"""
📋 Routes Offres
================
"""

from fastapi import APIRouter, HTTPException
from typing import List

from api.models.offre import Offre, OffreCreate, OffreUpdate
from api.database.fake_data import offres_db, get_next_offre_id

router = APIRouter()


@router.get("/", response_model=List[Offre])
async def lister_offres():
    return list(offres_db.values())


@router.get("/{offre_id}", response_model=Offre)
async def get_offre(offre_id: int):
    if offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {offre_id} non trouvée")
    return offres_db[offre_id]


@router.post("/", response_model=Offre, status_code=201)
async def creer_offre(offre: OffreCreate):
    new_id = get_next_offre_id()
    offre_data = offre.model_dump()
    offre_data["id"] = new_id
    
    for key in ["type_contrat", "politique_teletravail", "date_debut_souhaitee"]:
        if key in offre_data and hasattr(offre_data[key], "value"):
            offre_data[key] = offre_data[key].value
    
    offres_db[new_id] = offre_data
    return offre_data


@router.put("/{offre_id}", response_model=Offre)
async def modifier_offre(offre_id: int, offre_update: OffreUpdate):
    if offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {offre_id} non trouvée")
    
    offre_actuelle = offres_db[offre_id]
    update_data = offre_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if hasattr(value, "value"):
            update_data[key] = value.value
    
    offre_actuelle.update(update_data)
    offres_db[offre_id] = offre_actuelle
    return offre_actuelle


@router.delete("/{offre_id}", status_code=204)
async def supprimer_offre(offre_id: int):
    if offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {offre_id} non trouvée")
    del offres_db[offre_id]
    return None
