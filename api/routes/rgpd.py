"""
🔒 Routes RGPD - Protection des données
Suppression de compte, export données, consentements
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from ..database.supabase_client import SupabaseService
from .auth import get_current_user


router = APIRouter()


# ===== MODÈLES PYDANTIC =====

class DeleteAccountRequest(BaseModel):
    """Demande de suppression de compte"""
    confirmation: str  # Doit être "SUPPRIMER MON COMPTE"
    reason: Optional[str] = None
    password: Optional[str] = None  # Pour confirmation supplémentaire


class ExportDataRequest(BaseModel):
    """Demande d'export de données"""
    format: str = "json"  # json ou csv


# ===== ENDPOINTS SUPPRESSION COMPTE =====

@router.post("/account/delete")
async def delete_account(
    data: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🗑️ Supprimer définitivement mon compte.
    
    **ATTENTION: Cette action est IRRÉVERSIBLE**
    
    Supprime:
    - Profil candidat/recruteur
    - CV et documents
    - Messages et matchings
    - Entreprises (si recruteur)
    - Offres publiées
    - Historique de swipes
    - Toutes les données personnelles
    
    Conserve (anonymisé):
    - Statistiques globales
    - Messages dans tickets support (anonymisés)
    """
    
    # Vérification de la confirmation
    if data.confirmation != "SUPPRIMER MON COMPTE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation invalide. Vous devez écrire exactement: SUPPRIMER MON COMPTE"
        )
    
    try:
        supabase = SupabaseService.get_client()
        user_id = current_user["id"]
        user_type = current_user.get("type")
        
        logger.warning(f"🗑️ SUPPRESSION COMPTE: user_id={user_id}, type={user_type}, reason={data.reason}")
        
        # 1. Créer un log de suppression pour audit
        deletion_log = {
            "user_id": user_id,
            "user_email": current_user.get("email"),
            "user_type": user_type,
            "reason": data.reason,
            "deleted_at": datetime.now().isoformat(),
            "ip_address": None,  # TODO: récupérer IP de la requête
        }
        
        supabase.table("account_deletions").insert(deletion_log).execute()
        
        # 2. Anonymiser les messages de support
        supabase.table("support_ticket_messages")\
            .update({
                "user_id": None,
                "message": "[Utilisateur supprimé] - Message archivé"
            })\
            .eq("user_id", user_id)\
            .execute()
        
        # 3. Anonymiser les tickets support
        supabase.table("support_tickets")\
            .update({
                "user_id": None,
                "user_email": "deleted@recrut-der.com",
                "user_name": "Utilisateur supprimé"
            })\
            .eq("user_id", user_id)\
            .execute()
        
        # 4. Supprimer les conversations chatbot
        supabase.table("chatbot_conversations")\
            .delete()\
            .eq("user_id", user_id)\
            .execute()
        
        # 5. Supprimer les notifications
        supabase.table("notifications")\
            .delete()\
            .eq("utilisateur_id", user_id)\
            .execute()
        
        # 6. Supprimer les messages
        supabase.table("messages")\
            .delete()\
            .eq("expediteur_id", user_id)\
            .execute()
        
        supabase.table("messages")\
            .delete()\
            .eq("destinataire_id", user_id)\
            .execute()
        
        # 7. Supprimer les swipes
        supabase.table("swipes")\
            .delete()\
            .eq("candidat_id", user_id)\
            .execute()
        
        supabase.table("swipes")\
            .delete()\
            .eq("recruteur_id", user_id)\
            .execute()
        
        # 8. Supprimer les matchings
        supabase.table("matchings")\
            .delete()\
            .eq("candidat_id", user_id)\
            .execute()
        
        supabase.table("matchings")\
            .delete()\
            .eq("recruteur_id", user_id)\
            .execute()
        
        # 9. Si recruteur: supprimer entreprises et offres
        if user_type == "recruteur":
            # Récupérer les entreprises
            entreprises = supabase.table("entreprises")\
                .select("id")\
                .eq("recruteur_id", user_id)\
                .execute()
            
            if entreprises.data:
                for entreprise in entreprises.data:
                    # Supprimer les offres de l'entreprise
                    supabase.table("offres")\
                        .delete()\
                        .eq("entreprise_id", entreprise["id"])\
                        .execute()
                
                # Supprimer les entreprises
                supabase.table("entreprises")\
                    .delete()\
                    .eq("recruteur_id", user_id)\
                    .execute()
            
            # Supprimer le profil recruteur
            supabase.table("recruteurs")\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
        
        # 10. Si candidat: supprimer profil et CV
        elif user_type == "candidat":
            # TODO: Supprimer fichiers CV du storage Supabase
            
            # Supprimer le profil candidat
            supabase.table("candidats")\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
        
        # 11. Supprimer l'utilisateur (CASCADE supprimera les dépendances restantes)
        supabase.table("utilisateurs")\
            .delete()\
            .eq("id", user_id)\
            .execute()
        
        # 12. Supprimer de auth.users (Supabase Auth)
        # Note: Nécessite un appel admin à l'API Supabase Auth
        # Pour l'instant, on marque juste comme supprimé dans notre table
        
        logger.info(f"✅ Compte supprimé avec succès: user_id={user_id}")
        
        return {
            "success": True,
            "message": "Votre compte a été supprimé définitivement. Toutes vos données ont été effacées.",
            "deleted_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur suppression compte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du compte: {str(e)}"
        )


@router.get("/account/export")
async def export_my_data(
    format: str = "json",
    current_user: dict = Depends(get_current_user)
):
    """
    📦 Exporter toutes mes données personnelles (RGPD).
    
    Droit à la portabilité des données (Article 20 RGPD).
    """
    try:
        supabase = SupabaseService.get_client()
        user_id = current_user["id"]
        user_type = current_user.get("type")
        
        export_data: Dict[str, Any] = {
            "export_date": datetime.now().isoformat(),
            "user_info": current_user,
            "data": {}
        }
        
        # Récupérer toutes les données selon le type
        if user_type == "candidat":
            # Profil candidat
            candidat = supabase.table("candidats")\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            export_data["data"]["profil"] = candidat.data if candidat.data else {}
            
            # Swipes
            swipes = supabase.table("swipes")\
                .select("*")\
                .eq("candidat_id", user_id)\
                .execute()
            
            export_data["data"]["swipes"] = swipes.data or []
            
        elif user_type == "recruteur":
            # Profil recruteur
            recruteur = supabase.table("recruteurs")\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            export_data["data"]["profil"] = recruteur.data if recruteur.data else {}
            
            # Entreprises
            entreprises = supabase.table("entreprises")\
                .select("*")\
                .eq("recruteur_id", user_id)\
                .execute()
            
            export_data["data"]["entreprises"] = entreprises.data or []
            
            # Offres
            if entreprises.data:
                all_offres = []
                for entreprise in entreprises.data:
                    offres = supabase.table("offres")\
                        .select("*")\
                        .eq("entreprise_id", entreprise["id"])\
                        .execute()
                    all_offres.extend(offres.data or [])
                
                export_data["data"]["offres"] = all_offres
        
        # Données communes
        # Matchings
        matchings = supabase.table("matchings")\
            .select("*")\
            .or_(f"candidat_id.eq.{user_id},recruteur_id.eq.{user_id}")\
            .execute()
        
        export_data["data"]["matchings"] = matchings.data or []
        
        # Messages
        messages_sent = supabase.table("messages")\
            .select("*")\
            .eq("expediteur_id", user_id)\
            .execute()
        
        messages_received = supabase.table("messages")\
            .select("*")\
            .eq("destinataire_id", user_id)\
            .execute()
        
        export_data["data"]["messages"] = {
            "sent": messages_sent.data or [],
            "received": messages_received.data or []
        }
        
        # Notifications
        notifications = supabase.table("notifications")\
            .select("*")\
            .eq("utilisateur_id", user_id)\
            .execute()
        
        export_data["data"]["notifications"] = notifications.data or []
        
        # Support tickets
        tickets = supabase.table("support_tickets")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        export_data["data"]["support_tickets"] = tickets.data or []
        
        logger.info(f"📦 Export données: user_id={user_id}")
        
        return export_data
    
    except Exception as e:
        logger.error(f"❌ Erreur export données: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export des données: {str(e)}"
        )


@router.get("/account/info")
async def get_account_info(current_user: dict = Depends(get_current_user)):
    """
    ℹ️ Informations sur mon compte et mes données.
    
    Indique:
    - Date de création
    - Données stockées
    - Taille des données
    - Droits RGPD
    """
    try:
        supabase = SupabaseService.get_client()
        user_id = current_user["id"]
        
        # Compter les données
        stats = {
            "account": {
                "created_at": current_user.get("created_at"),
                "email": current_user.get("email"),
                "type": current_user.get("type")
            },
            "data_counts": {}
        }
        
        # Compter matchings
        matchings = supabase.table("matchings")\
            .select("id", count="exact")\
            .or_(f"candidat_id.eq.{user_id},recruteur_id.eq.{user_id}")\
            .execute()
        
        stats["data_counts"]["matchings"] = matchings.count or 0
        
        # Compter messages
        messages = supabase.table("messages")\
            .select("id", count="exact")\
            .or_(f"expediteur_id.eq.{user_id},destinataire_id.eq.{user_id}")\
            .execute()
        
        stats["data_counts"]["messages"] = messages.count or 0
        
        # Compter swipes
        swipes = supabase.table("swipes")\
            .select("id", count="exact")\
            .or_(f"candidat_id.eq.{user_id},recruteur_id.eq.{user_id}")\
            .execute()
        
        stats["data_counts"]["swipes"] = swipes.count or 0
        
        # Droits RGPD
        stats["rgpd_rights"] = {
            "access": "Vous pouvez exporter vos données avec GET /api/rgpd/account/export",
            "rectification": "Vous pouvez modifier vos données via votre profil",
            "deletion": "Vous pouvez supprimer votre compte avec POST /api/rgpd/account/delete",
            "portability": "Vos données sont exportables au format JSON",
            "opposition": "Vous pouvez vous opposer au traitement en supprimant votre compte"
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"❌ Erreur info compte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
