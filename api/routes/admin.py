"""
👑 Routes API pour le Dashboard Administrateur
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..database.supabase_client import SupabaseService


router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def get_supabase_client():
    """Dependency pour obtenir le client Supabase"""
    return SupabaseService.get_client()


async def verify_admin(authorization: str = Header(...)):
    """
    Vérifier que l'utilisateur est administrateur.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token invalide")
    
    token = authorization.replace("Bearer ", "")
    supabase = get_supabase_client()
    
    try:
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        user_id = user_response.user.id
        
        # Vérifier si l'utilisateur est admin dans la table utilisateurs
        user_data = supabase.table("utilisateurs").select("role").eq("id", user_id).execute()
        
        if not user_data.data or user_data.data[0].get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        return {"id": user_id, "email": user_response.user.email, "role": "admin"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur vérification admin: {str(e)}")
        raise HTTPException(status_code=403, detail="Accès refusé")


# ═══════════════════════════════════════════════════════════════════
# 📊 VUE D'ENSEMBLE & KPIs
# ═══════════════════════════════════════════════════════════════════

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    📊 Vue d'ensemble du dashboard avec KPIs principaux.
    
    Retourne:
    - Nombre total d'utilisateurs (candidats, recruteurs, admins)
    - Nombre d'offres actives
    - Nombre de matchs créés
    - Taux de matching global
    - Activité des 7 derniers jours
    - Croissance utilisateurs
    """
    try:
        # Compter les utilisateurs
        candidats = supabase.table("candidats").select("id", count="exact").execute()
        recruteurs = supabase.table("recruteurs").select("id", count="exact").execute()
        
        total_candidats = candidats.count if candidats else 0
        total_recruteurs = recruteurs.count if recruteurs else 0
        
        # Compter les offres actives
        offres_actives = supabase.table("offres").select("id", count="exact").eq("publiee", True).execute()
        total_offres_actives = offres_actives.count if offres_actives else 0
        
        # Compter les matchs
        matches = supabase.table("matchings").select("id", count="exact").execute()
        total_matches = matches.count if matches else 0
        
        # Compter les swipes
        swipes = supabase.table("swipes").select("id", count="exact").execute()
        total_swipes = swipes.count if swipes else 0
        
        # Calculer le taux de matching
        likes = supabase.table("swipes").select("id", count="exact").eq("action", "like").execute()
        total_likes = likes.count if likes else 0
        match_rate = (total_matches / total_likes * 100) if total_likes > 0 else 0
        
        # Activité des 7 derniers jours
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        new_users_week = supabase.table("candidats").select("id", count="exact").gte("created_at", seven_days_ago).execute()
        new_matches_week = supabase.table("matchings").select("id", count="exact").gte("created_at", seven_days_ago).execute()
        
        total_new_users_week = (new_users_week.count if new_users_week else 0)
        total_new_matches_week = (new_matches_week.count if new_matches_week else 0)
        
        # Tickets de support ouverts
        tickets_ouverts = supabase.table("support_tickets").select("id", count="exact").eq("status", "open").execute()
        total_tickets_ouverts = tickets_ouverts.count if tickets_ouverts else 0
        
        return {
            "success": True,
            "kpis": {
                "total_utilisateurs": total_candidats + total_recruteurs,
                "total_candidats": total_candidats,
                "total_recruteurs": total_recruteurs,
                "total_offres_actives": total_offres_actives,
                "total_matches": total_matches,
                "total_swipes": total_swipes,
                "match_rate": round(match_rate, 1),
                "tickets_ouverts": total_tickets_ouverts
            },
            "activite_7j": {
                "nouveaux_utilisateurs": total_new_users_week,
                "nouveaux_matches": total_new_matches_week
            }
        }
    
    except Exception as e:
        logger.error(f"Erreur dashboard overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/dashboard/stats-daily")
async def get_daily_stats(
    days: int = Query(default=30, ge=1, le=365),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    📈 Statistiques journalières pour graphiques.
    
    Retourne les données des X derniers jours:
    - Nouveaux utilisateurs par jour
    - Nouveaux matchs par jour
    - Swipes par jour
    """
    try:
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Récupérer tous les candidats créés dans la période
        candidats = supabase.table("candidats").select("created_at").gte("created_at", start_date).execute()
        
        # Récupérer tous les matchs dans la période
        matches = supabase.table("matchings").select("created_at").gte("created_at", start_date).execute()
        
        # Récupérer tous les swipes dans la période
        swipes = supabase.table("swipes").select("created_at").gte("created_at", start_date).execute()
        
        # Grouper par jour (simplifié - à améliorer avec SQL GROUP BY)
        daily_data = {}
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data[date] = {
                "date": date,
                "nouveaux_utilisateurs": 0,
                "nouveaux_matches": 0,
                "total_swipes": 0
            }
        
        # Compter les utilisateurs par jour
        if candidats.data:
            for candidat in candidats.data:
                date = candidat["created_at"][:10]
                if date in daily_data:
                    daily_data[date]["nouveaux_utilisateurs"] += 1
        
        # Compter les matchs par jour
        if matches.data:
            for match in matches.data:
                date = match["created_at"][:10]
                if date in daily_data:
                    daily_data[date]["nouveaux_matches"] += 1
        
        # Compter les swipes par jour
        if swipes.data:
            for swipe in swipes.data:
                date = swipe["created_at"][:10]
                if date in daily_data:
                    daily_data[date]["total_swipes"] += 1
        
        # Convertir en liste triée
        stats_list = sorted(daily_data.values(), key=lambda x: x["date"])
        
        return {
            "success": True,
            "period_days": days,
            "stats": stats_list
        }
    
    except Exception as e:
        logger.error(f"Erreur stats daily: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# 👥 GESTION DES UTILISATEURS
# ═══════════════════════════════════════════════════════════════════

@router.get("/users")
async def list_users(
    type_user: Optional[str] = Query(None, regex="^(candidat|recruteur)$"),
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    👥 Lister tous les utilisateurs avec pagination et filtres.
    """
    try:
        offset = (page - 1) * limit
        
        if type_user == "candidat":
            query = supabase.table("candidats").select("*")
            
            if search:
                # Recherche basique (à améliorer avec full-text search)
                query = query.or_(f"nom.ilike.%{search}%,prenom.ilike.%{search}%,email.ilike.%{search}%")
            
            result = query.range(offset, offset + limit - 1).execute()
            
            return {
                "success": True,
                "type": "candidat",
                "count": len(result.data) if result.data else 0,
                "page": page,
                "limit": limit,
                "users": result.data or []
            }
        
        elif type_user == "recruteur":
            query = supabase.table("recruteurs").select("*")
            
            if search:
                query = query.or_(f"nom.ilike.%{search}%,email.ilike.%{search}%,entreprise.ilike.%{search}%")
            
            result = query.range(offset, offset + limit - 1).execute()
            
            return {
                "success": True,
                "type": "recruteur",
                "count": len(result.data) if result.data else 0,
                "page": page,
                "limit": limit,
                "users": result.data or []
            }
        
        else:
            # Retourner tous les utilisateurs (candidats + recruteurs)
            candidats = supabase.table("candidats").select("*").range(offset, offset + limit - 1).execute()
            recruteurs = supabase.table("recruteurs").select("*").range(offset, offset + limit - 1).execute()
            
            all_users = []
            
            if candidats.data:
                for c in candidats.data:
                    all_users.append({**c, "user_type": "candidat"})
            
            if recruteurs.data:
                for r in recruteurs.data:
                    all_users.append({**r, "user_type": "recruteur"})
            
            return {
                "success": True,
                "type": "all",
                "count": len(all_users),
                "page": page,
                "limit": limit,
                "users": all_users
            }
    
    except Exception as e:
        logger.error(f"Erreur list users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    🔍 Obtenir le détail complet d'un utilisateur.
    """
    try:
        # Chercher dans candidats
        candidat = supabase.table("candidats").select("*").eq("id", user_id).execute()
        
        if candidat.data:
            user_data = candidat.data[0]
            
            # Récupérer les swipes du candidat
            swipes = supabase.table("swipes").select("*").eq("candidat_id", user_id).execute()
            
            # Récupérer les matchs
            matches = supabase.table("matchings").select("*").eq("candidat_id", user_id).execute()
            
            return {
                "success": True,
                "user_type": "candidat",
                "user": user_data,
                "stats": {
                    "total_swipes": len(swipes.data) if swipes.data else 0,
                    "total_matches": len(matches.data) if matches.data else 0
                }
            }
        
        # Chercher dans recruteurs
        recruteur = supabase.table("recruteurs").select("*").eq("id", user_id).execute()
        
        if recruteur.data:
            user_data = recruteur.data[0]
            
            # Récupérer les offres du recruteur
            offres = supabase.table("offres").select("*").eq("recruteur_id", user_id).execute()
            
            return {
                "success": True,
                "user_type": "recruteur",
                "user": user_data,
                "stats": {
                    "total_offres": len(offres.data) if offres.data else 0
                }
            }
        
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get user detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    raison: str = Query(..., min_length=10),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    🚫 Suspendre un utilisateur (candidat ou recruteur).
    """
    try:
        # Vérifier si candidat
        candidat = supabase.table("candidats").select("id").eq("id", user_id).execute()
        
        if candidat.data:
            # Suspendre le candidat
            supabase.table("candidats").update({
                "actif": False,
                "suspendu": True,
                "raison_suspension": raison,
                "suspendu_le": datetime.now().isoformat()
            }).eq("id", user_id).execute()
            
            # Logger l'action
            supabase.table("admin_logs").insert({
                "admin_id": admin_user["id"],
                "action": "suspend_user",
                "cible_type": "candidat",
                "cible_id": user_id,
                "details": {"raison": raison},
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {
                "success": True,
                "message": "Candidat suspendu avec succès",
                "user_type": "candidat",
                "user_id": user_id
            }
        
        # Vérifier si recruteur
        recruteur = supabase.table("recruteurs").select("id").eq("id", user_id).execute()
        
        if recruteur.data:
            # Suspendre le recruteur
            supabase.table("recruteurs").update({
                "actif": False,
                "suspendu": True,
                "raison_suspension": raison,
                "suspendu_le": datetime.now().isoformat()
            }).eq("id", user_id).execute()
            
            # Logger l'action
            supabase.table("admin_logs").insert({
                "admin_id": admin_user["id"],
                "action": "suspend_user",
                "cible_type": "recruteur",
                "cible_id": user_id,
                "details": {"raison": raison},
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {
                "success": True,
                "message": "Recruteur suspendu avec succès",
                "user_type": "recruteur",
                "user_id": user_id
            }
        
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suspend user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    ✅ Réactiver un utilisateur suspendu.
    """
    try:
        # Chercher dans candidats
        candidat = supabase.table("candidats").select("id").eq("id", user_id).execute()
        
        if candidat.data:
            supabase.table("candidats").update({
                "actif": True,
                "suspendu": False,
                "raison_suspension": None,
                "suspendu_le": None
            }).eq("id", user_id).execute()
            
            # Logger
            supabase.table("admin_logs").insert({
                "admin_id": admin_user["id"],
                "action": "reactivate_user",
                "cible_type": "candidat",
                "cible_id": user_id,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {
                "success": True,
                "message": "Candidat réactivé avec succès"
            }
        
        # Chercher dans recruteurs
        recruteur = supabase.table("recruteurs").select("id").eq("id", user_id).execute()
        
        if recruteur.data:
            supabase.table("recruteurs").update({
                "actif": True,
                "suspendu": False,
                "raison_suspension": None,
                "suspendu_le": None
            }).eq("id", user_id).execute()
            
            # Logger
            supabase.table("admin_logs").insert({
                "admin_id": admin_user["id"],
                "action": "reactivate_user",
                "cible_type": "recruteur",
                "cible_id": user_id,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {
                "success": True,
                "message": "Recruteur réactivé avec succès"
            }
        
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur reactivate user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# 📋 GESTION DES OFFRES
# ═══════════════════════════════════════════════════════════════════

@router.get("/offres")
async def list_offres(
    statut: Optional[str] = Query(None, regex="^(brouillon|publiee|expiree|suspendue)$"),
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    📋 Lister toutes les offres avec filtres.
    """
    try:
        offset = (page - 1) * limit
        
        query = supabase.table("offres").select("*")
        
        if statut:
            query = query.eq("statut", statut)
        
        if search:
            query = query.or_(f"titre.ilike.%{search}%,description.ilike.%{search}%,entreprise.ilike.%{search}%")
        
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "count": len(result.data) if result.data else 0,
            "page": page,
            "limit": limit,
            "offres": result.data or []
        }
    
    except Exception as e:
        logger.error(f"Erreur list offres: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/offres/{offre_id}/suspend")
async def suspend_offre(
    offre_id: str,
    raison: str = Query(..., min_length=10),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    🚫 Suspendre une offre d'emploi.
    """
    try:
        supabase.table("offres").update({
            "statut": "suspendue",
            "raison_suspension": raison,
            "suspendue_le": datetime.now().isoformat()
        }).eq("id", offre_id).execute()
        
        # Logger
        supabase.table("admin_logs").insert({
            "admin_id": admin_user["id"],
            "action": "suspend_offre",
            "cible_type": "offre",
            "cible_id": offre_id,
            "details": {"raison": raison},
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "Offre suspendue avec succès"
        }
    
    except Exception as e:
        logger.error(f"Erreur suspend offre: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# 🎫 GESTION DES TICKETS DE SUPPORT
# ═══════════════════════════════════════════════════════════════════

@router.get("/support/tickets")
async def list_tickets(
    status: Optional[str] = Query(None, regex="^(open|in_progress|waiting_user|resolved|closed)$"),
    priorite: Optional[str] = Query(None, regex="^(basse|normale|haute|urgente)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    🎫 Lister tous les tickets de support.
    """
    try:
        offset = (page - 1) * limit
        
        query = supabase.table("support_tickets").select("*")
        
        if status:
            query = query.eq("status", status)
        
        if priorite:
            query = query.eq("priorite", priorite)
        
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "count": len(result.data) if result.data else 0,
            "page": page,
            "limit": limit,
            "tickets": result.data or []
        }
    
    except Exception as e:
        logger.error(f"Erreur list tickets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/support/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    👤 S'assigner un ticket de support.
    """
    try:
        supabase.table("support_tickets").update({
            "assigned_to": admin_user["id"],
            "status": "in_progress",
            "updated_at": datetime.now().isoformat()
        }).eq("id", ticket_id).execute()
        
        return {
            "success": True,
            "message": "Ticket assigné avec succès"
        }
    
    except Exception as e:
        logger.error(f"Erreur assign ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/support/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution: str = Query(..., min_length=10),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    ✅ Résoudre un ticket de support.
    """
    try:
        supabase.table("support_tickets").update({
            "status": "resolved",
            "resolution": resolution,
            "resolved_by": admin_user["id"],
            "resolved_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).eq("id", ticket_id).execute()
        
        # Logger
        supabase.table("admin_logs").insert({
            "admin_id": admin_user["id"],
            "action": "resolve_ticket",
            "cible_type": "support_ticket",
            "cible_id": ticket_id,
            "details": {"resolution": resolution},
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "Ticket résolu avec succès"
        }
    
    except Exception as e:
        logger.error(f"Erreur resolve ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# 📝 LOGS & AUDIT
# ═══════════════════════════════════════════════════════════════════

@router.get("/logs")
async def get_admin_logs(
    action: Optional[str] = None,
    admin_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    admin_user: dict = Depends(verify_admin),
    supabase = Depends(get_supabase_client)
):
    """
    📝 Récupérer les logs d'administration.
    """
    try:
        offset = (page - 1) * limit
        
        query = supabase.table("admin_logs").select("*")
        
        if action:
            query = query.eq("action", action)
        
        if admin_id:
            query = query.eq("admin_id", admin_id)
        
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "count": len(result.data) if result.data else 0,
            "page": page,
            "limit": limit,
            "logs": result.data or []
        }
    
    except Exception as e:
        logger.error(f"Erreur get logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
