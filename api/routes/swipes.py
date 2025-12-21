"""
👍 Recrut'der - Routes Swipes (Type Tinder)
============================================
Like/Dislike candidats et offres + Matching automatique
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID

from api.models.v2_models import SwipeCreate, SwipeResponse
from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from loguru import logger


router = APIRouter()


@router.post("/", response_model=SwipeResponse, status_code=status.HTTP_201_CREATED)
async def create_swipe(
    swipe_data: SwipeCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    👍 Swiper sur un candidat ou une offre (like/dislike/super_like)
    
    - Candidat peut swiper sur une offre
    - Recruteur peut swiper sur un candidat
    - Si les 2 ont liké → Match automatique !
    """
    try:
        # Préparer les données du swipe
        swipe_insert = {
            "user_id": current_user["id"],
            "type_swipe": swipe_data.type_swipe.value,
            "action": swipe_data.action.value,
            "candidat_id": str(swipe_data.candidat_id) if swipe_data.candidat_id else None,
            "offre_id": str(swipe_data.offre_id) if swipe_data.offre_id else None
        }
        
        # Créer le swipe (le trigger SQL va automatiquement checker le match)
        result = supabase.table("swipes")\
            .insert(swipe_insert)\
            .execute()
        
        swipe = result.data[0]
        
        if swipe.get("is_match"):
            logger.info(f"🎉 MATCH ! Swipe ID: {swipe['id']}")
        else:
            logger.info(f"👍 Swipe créé: {swipe_data.action.value}")
        
        return swipe
        
    except Exception as e:
        logger.error(f"❌ Erreur création swipe: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous avez déjà swipé sur cet élément"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-swipes", response_model=List[SwipeResponse])
async def get_my_swipes(
    current_user: dict = Depends(get_current_user),
    matches_only: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """
    📋 Récupérer mes swipes
    
    - matches_only=true : Uniquement les matchs
    - matches_only=false : Tous mes swipes
    """
    try:
        query = supabase.table("swipes")\
            .select("*")\
            .eq("user_id", current_user["id"])
        
        if matches_only:
            query = query.eq("is_match", True)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération swipes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/matches/count")
async def count_my_matches(current_user: dict = Depends(get_current_user)):
    """
    🔢 Compter le nombre de matchs
    """
    try:
        result = supabase.table("swipes")\
            .select("*", count="exact")\
            .eq("user_id", current_user["id"])\
            .eq("is_match", True)\
            .execute()
        
        return {"count": result.count}
        
    except Exception as e:
        logger.error(f"❌ Erreur comptage matchs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/candidat/{candidat_id}/next-offres", response_model=List[dict])
async def get_next_offres_to_swipe(
    candidat_id: UUID,
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    📱 Récupérer la prochaine pile d'offres à swiper pour un candidat
    
    Retourne les offres que le candidat n'a pas encore swipées.
    """
    try:
        # Vérifier que l'utilisateur est bien ce candidat
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("id", str(candidat_id))\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé"
            )
        
        # Récupérer les offres déjà swipées
        swipes = supabase.table("swipes")\
            .select("offre_id")\
            .eq("user_id", current_user["id"])\
            .eq("type_swipe", "candidat_to_offre")\
            .execute()
        
        swiped_offre_ids = [s["offre_id"] for s in swipes.data if s["offre_id"]]
        
        # Récupérer les offres non swipées
        query = supabase.table("offres")\
            .select("*")\
            .eq("publiee", True)
        
        if swiped_offre_ids:
            query = query.not_.in_("id", swiped_offre_ids)
        
        result = query.limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération offres à swiper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/offre/{offre_id}/next-candidats", response_model=List[dict])
async def get_next_candidats_to_swipe(
    offre_id: UUID,
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    📱 Récupérer la prochaine pile de candidats à swiper pour une offre
    
    Retourne les candidats que le recruteur n'a pas encore swipés pour cette offre.
    """
    try:
        # Vérifier que l'utilisateur est le recruteur de cette offre
        offre = supabase.table("offres")\
            .select("*, recruteurs!inner(user_id)")\
            .eq("id", str(offre_id))\
            .single()\
            .execute()
        
        if not offre.data or offre.data["recruteurs"]["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé"
            )
        
        # Récupérer les candidats déjà swipés pour cette offre
        swipes = supabase.table("swipes")\
            .select("candidat_id")\
            .eq("user_id", current_user["id"])\
            .eq("type_swipe", "recruteur_to_candidat")\
            .eq("offre_id", str(offre_id))\
            .execute()
        
        swiped_candidat_ids = [s["candidat_id"] for s in swipes.data if s["candidat_id"]]
        
        # Récupérer les candidats non swipés
        query = supabase.table("candidats")\
            .select("*")\
            .eq("actif", True)
        
        if swiped_candidat_ids:
            query = query.not_.in_("id", swiped_candidat_ids)
        
        result = query.limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération candidats à swiper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
