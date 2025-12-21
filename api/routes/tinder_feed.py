"""
🎯 Routes API pour le feed de recommandations type Tinder
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime
import json

from ..database.supabase_client import SupabaseService
from ..services.tinder_matching import TinderMatchingEngine
from loguru import logger


router = APIRouter(prefix="/tinder", tags=["Tinder Feed"])


def get_supabase_client():
    """Dependency pour obtenir le client Supabase"""
    return SupabaseService.get_client()


async def get_current_user(authorization: str = Header(...)):
    """
    Récupérer l'utilisateur courant depuis le token JWT.
    Simplifié pour éviter les dépendances circulaires.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token invalide")
    
    token = authorization.replace("Bearer ", "")
    supabase = get_supabase_client()
    
    try:
        # Vérifier le token avec Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        return {"id": user_response.user.id, "email": user_response.user.email}
    
    except Exception as e:
        logger.error(f"Erreur auth: {str(e)}")
        raise HTTPException(status_code=401, detail="Non authentifié")


@router.get("/feed")
async def get_feed(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    📱 Obtenir le feed de recommandations type Tinder.
    
    - Candidat → reçoit des offres d'emploi
    - Recruteur → reçoit des profils de candidats
    
    Le feed est intelligent:
    - Top matches en priorité
    - Diversification (pas toujours les mêmes)
    - Apprentissage des préférences
    - Bonus fraîcheur
    """
    try:
        user_id = current_user["id"]
        
        # Déterminer le type d'utilisateur
        candidat_data = supabase.table("candidats").select("*").eq("user_id", user_id).execute()
        is_candidat = bool(candidat_data.data)
        
        if is_candidat:
            # Candidat → feed d'offres
            candidat = candidat_data.data[0]
            
            # Récupérer toutes les offres actives
            offres_response = supabase.table("offres").select("*").eq("statut", "publiee").execute()
            all_offers = offres_response.data or []
            
            # Récupérer les swipes déjà effectués
            swipes_response = supabase.table("swipes").select("offre_id").eq("candidat_id", candidat["id"]).execute()
            already_swiped = [s["offre_id"] for s in swipes_response.data] if swipes_response.data else []
            
            # Récupérer l'historique complet des swipes pour l'apprentissage
            history_response = supabase.table("swipes").select("*").eq("candidat_id", candidat["id"]).order("created_at", desc=True).limit(50).execute()
            swipe_history = history_response.data or []
            
            # Générer le feed intelligent
            recommendations = TinderMatchingEngine.get_recommendation_feed(
                user_id=user_id,
                user_type="candidat",
                user_profile=candidat,
                all_offers=all_offers,
                already_swiped=already_swiped,
                swipe_history=swipe_history,
                limit=limit
            )
            
            return {
                "success": True,
                "count": len(recommendations),
                "user_type": "candidat",
                "recommendations": recommendations
            }
        
        else:
            # Recruteur → feed de candidats
            recruteur_data = supabase.table("recruteurs").select("*").eq("user_id", user_id).execute()
            if not recruteur_data.data:
                raise HTTPException(status_code=404, detail="Profil recruteur non trouvé")
            
            recruteur = recruteur_data.data[0]
            
            # Récupérer les offres actives du recruteur
            offres_recruteur = supabase.table("offres").select("*").eq("recruteur_id", recruteur["id"]).eq("statut", "publiee").execute()
            
            if not offres_recruteur.data:
                return {
                    "success": True,
                    "count": 0,
                    "user_type": "recruteur",
                    "message": "Créez d'abord une offre pour recevoir des candidats",
                    "recommendations": []
                }
            
            # Pour simplifier, on prend la première offre active
            # TODO: permettre de choisir l'offre
            offre = offres_recruteur.data[0]
            
            # Récupérer tous les candidats actifs
            candidats_response = supabase.table("candidats").select("*").eq("recherche_active", True).execute()
            all_candidates = candidats_response.data or []
            
            # Récupérer les swipes déjà effectués pour cette offre
            swipes_response = supabase.table("swipes").select("candidat_id").eq("offre_id", offre["id"]).execute()
            already_swiped = [s["candidat_id"] for s in swipes_response.data] if swipes_response.data else []
            
            # Récupérer l'historique
            history_response = supabase.table("swipes").select("*").eq("offre_id", offre["id"]).order("created_at", desc=True).limit(50).execute()
            swipe_history = history_response.data or []
            
            # Générer le feed
            recommendations = TinderMatchingEngine.get_recommendation_feed(
                user_id=user_id,
                user_type="recruteur",
                user_profile=offre,
                all_candidates=all_candidates,
                already_swiped=already_swiped,
                swipe_history=swipe_history,
                limit=limit
            )
            
            return {
                "success": True,
                "count": len(recommendations),
                "user_type": "recruteur",
                "offre_selectionnee": offre["titre"],
                "recommendations": recommendations
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_feed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/match-detail/{item_id}")
async def get_match_detail(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    🔍 Obtenir le détail d'un match potentiel.
    
    Explique POURQUOI ce profil/offre correspond,
    avec scores détaillés et recommandations.
    """
    try:
        user_id = current_user["id"]
        
        # Déterminer le type d'utilisateur
        candidat_data = supabase.table("candidats").select("*").eq("user_id", user_id).execute()
        is_candidat = bool(candidat_data.data)
        
        if is_candidat:
            # Candidat → détail d'une offre
            candidat = candidat_data.data[0]
            
            offre_response = supabase.table("offres").select("*").eq("id", item_id).execute()
            if not offre_response.data:
                raise HTTPException(status_code=404, detail="Offre non trouvée")
            
            offre = offre_response.data[0]
            
            # Calculer le score détaillé
            match_data = TinderMatchingEngine.calculate_smart_score(
                candidat=candidat,
                offre=offre
            )
            
            return {
                "success": True,
                "type": "offre",
                "item": offre,
                "match_data": match_data
            }
        
        else:
            # Recruteur → détail d'un candidat
            candidat_response = supabase.table("candidats").select("*").eq("id", item_id).execute()
            if not candidat_response.data:
                raise HTTPException(status_code=404, detail="Candidat non trouvé")
            
            candidat = candidat_response.data[0]
            
            # Récupérer l'offre active du recruteur
            recruteur_data = supabase.table("recruteurs").select("*").eq("user_id", user_id).execute()
            if not recruteur_data.data:
                raise HTTPException(status_code=404, detail="Profil recruteur non trouvé")
            
            recruteur = recruteur_data.data[0]
            offres_recruteur = supabase.table("offres").select("*").eq("recruteur_id", recruteur["id"]).eq("statut", "publiee").execute()
            
            if not offres_recruteur.data:
                raise HTTPException(status_code=404, detail="Aucune offre active")
            
            offre = offres_recruteur.data[0]
            
            # Calculer le score
            match_data = TinderMatchingEngine.calculate_smart_score(
                candidat=candidat,
                offre=offre
            )
            
            return {
                "success": True,
                "type": "candidat",
                "item": candidat,
                "match_data": match_data
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_match_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/swipe")
async def swipe_item(
    item_id: str,
    action: str = Query(..., regex="^(like|dislike)$"),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    👆 Swiper sur un profil/offre (like ou dislike).
    
    Si les deux parties likent → MATCH! 🎉
    """
    try:
        user_id = current_user["id"]
        
        # Déterminer le type d'utilisateur
        candidat_data = supabase.table("candidats").select("*").eq("user_id", user_id).execute()
        is_candidat = bool(candidat_data.data)
        
        if is_candidat:
            # Candidat swipe une offre
            candidat = candidat_data.data[0]
            
            # Vérifier que l'offre existe
            offre_check = supabase.table("offres").select("id").eq("id", item_id).execute()
            if not offre_check.data:
                raise HTTPException(status_code=404, detail="Offre non trouvée")
            
            # Créer le swipe
            swipe_data = {
                "candidat_id": candidat["id"],
                "offre_id": item_id,
                "action": action,
                "created_at": datetime.now().isoformat()
            }
            
            swipe_result = supabase.table("swipes").insert(swipe_data).execute()
            
            # Vérifier si c'est un match (trigger SQL le gère automatiquement)
            if action == "like":
                match_check = supabase.table("matches").select("*").eq("candidat_id", candidat["id"]).eq("offre_id", item_id).execute()
                
                is_match = bool(match_check.data)
                
                return {
                    "success": True,
                    "action": action,
                    "is_match": is_match,
                    "message": "🎉 C'EST UN MATCH!" if is_match else "Swipe enregistré",
                    "swipe": swipe_result.data[0] if swipe_result.data else None
                }
            else:
                return {
                    "success": True,
                    "action": action,
                    "is_match": False,
                    "message": "Swipe enregistré"
                }
        
        else:
            # Recruteur swipe un candidat
            recruteur_data = supabase.table("recruteurs").select("*").eq("user_id", user_id).execute()
            if not recruteur_data.data:
                raise HTTPException(status_code=404, detail="Profil recruteur non trouvé")
            
            recruteur = recruteur_data.data[0]
            
            # Récupérer l'offre active
            offres_recruteur = supabase.table("offres").select("*").eq("recruteur_id", recruteur["id"]).eq("statut", "publiee").execute()
            if not offres_recruteur.data:
                raise HTTPException(status_code=404, detail="Aucune offre active")
            
            offre = offres_recruteur.data[0]
            
            # Vérifier que le candidat existe
            candidat_check = supabase.table("candidats").select("id").eq("id", item_id).execute()
            if not candidat_check.data:
                raise HTTPException(status_code=404, detail="Candidat non trouvé")
            
            # Créer le swipe
            swipe_data = {
                "candidat_id": item_id,
                "offre_id": offre["id"],
                "action": action,
                "created_at": datetime.now().isoformat()
            }
            
            swipe_result = supabase.table("swipes").insert(swipe_data).execute()
            
            # Vérifier le match
            if action == "like":
                match_check = supabase.table("matches").select("*").eq("candidat_id", item_id).eq("offre_id", offre["id"]).execute()
                
                is_match = bool(match_check.data)
                
                return {
                    "success": True,
                    "action": action,
                    "is_match": is_match,
                    "message": "🎉 C'EST UN MATCH!" if is_match else "Swipe enregistré",
                    "swipe": swipe_result.data[0] if swipe_result.data else None
                }
            else:
                return {
                    "success": True,
                    "action": action,
                    "is_match": False,
                    "message": "Swipe enregistré"
                }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur swipe_item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    📊 Statistiques de matching de l'utilisateur.
    
    - Nombre de swipes
    - Taux de match
    - Profils vus
    - etc.
    """
    try:
        user_id = current_user["id"]
        
        # Déterminer le type d'utilisateur
        candidat_data = supabase.table("candidats").select("*").eq("user_id", user_id).execute()
        is_candidat = bool(candidat_data.data)
        
        if is_candidat:
            candidat = candidat_data.data[0]
            
            # Stats candidat
            swipes = supabase.table("swipes").select("*").eq("candidat_id", candidat["id"]).execute()
            matches = supabase.table("matches").select("*").eq("candidat_id", candidat["id"]).execute()
            
            total_swipes = len(swipes.data) if swipes.data else 0
            total_likes = len([s for s in (swipes.data or []) if s["action"] == "like"])
            total_matches = len(matches.data) if matches.data else 0
            
            match_rate = (total_matches / total_likes * 100) if total_likes > 0 else 0
            
            return {
                "success": True,
                "user_type": "candidat",
                "stats": {
                    "total_swipes": total_swipes,
                    "total_likes": total_likes,
                    "total_dislikes": total_swipes - total_likes,
                    "total_matches": total_matches,
                    "match_rate": round(match_rate, 1)
                }
            }
        
        else:
            recruteur_data = supabase.table("recruteurs").select("*").eq("user_id", user_id).execute()
            if not recruteur_data.data:
                raise HTTPException(status_code=404, detail="Profil recruteur non trouvé")
            
            recruteur = recruteur_data.data[0]
            
            # Stats recruteur (toutes offres confondues)
            offres = supabase.table("offres").select("id").eq("recruteur_id", recruteur["id"]).execute()
            offre_ids = [o["id"] for o in (offres.data or [])]
            
            if not offre_ids:
                return {
                    "success": True,
                    "user_type": "recruteur",
                    "stats": {
                        "total_swipes": 0,
                        "total_likes": 0,
                        "total_dislikes": 0,
                        "total_matches": 0,
                        "match_rate": 0
                    }
                }
            
            # Compter les swipes sur toutes les offres
            all_swipes = []
            all_matches = []
            
            for offre_id in offre_ids:
                swipes = supabase.table("swipes").select("*").eq("offre_id", offre_id).execute()
                matches = supabase.table("matches").select("*").eq("offre_id", offre_id).execute()
                
                if swipes.data:
                    all_swipes.extend(swipes.data)
                if matches.data:
                    all_matches.extend(matches.data)
            
            total_swipes = len(all_swipes)
            total_likes = len([s for s in all_swipes if s["action"] == "like"])
            total_matches = len(all_matches)
            
            match_rate = (total_matches / total_likes * 100) if total_likes > 0 else 0
            
            return {
                "success": True,
                "user_type": "recruteur",
                "stats": {
                    "total_swipes": total_swipes,
                    "total_likes": total_likes,
                    "total_dislikes": total_swipes - total_likes,
                    "total_matches": total_matches,
                    "match_rate": round(match_rate, 1)
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
