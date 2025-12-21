"""
📞 Routes Contact Direct
Email, messagerie interne, rendez-vous visio
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from loguru import logger
from datetime import datetime, timedelta
import uuid

from ..database.supabase_client import SupabaseService
from .auth import get_current_user


router = APIRouter()


# ===== MODÈLES PYDANTIC =====

class SendEmailRequest(BaseModel):
    """Envoi d'email direct"""
    recipient_id: str = Field(..., description="ID du destinataire")
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10)
    copy_to_internal: bool = Field(True, description="Copier dans messagerie interne")


class ScheduleMeetingRequest(BaseModel):
    """Planifier un rendez-vous visio"""
    recipient_id: str = Field(..., description="ID du destinataire")
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    scheduled_at: str = Field(..., description="Date/heure du RDV (ISO 8601)")
    duration_minutes: int = Field(30, ge=15, le=180)
    meeting_type: str = Field("video", pattern="^(video|phone|in_person)$")


class UpdateMeetingRequest(BaseModel):
    """Mise à jour d'un RDV"""
    status: Optional[str] = Field(None, pattern="^(confirmed|cancelled|completed|rescheduled)$")
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None


# ===== ENDPOINTS EMAIL =====

@router.post("/email/send")
async def send_direct_email(
    data: SendEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    📧 Envoyer un email direct à un utilisateur.
    
    L'email est envoyé via service externe (SendGrid, Mailgun, etc.)
    et optionnellement copié dans la messagerie interne.
    """
    try:
        supabase = SupabaseService.get_client()
        
        # Vérifier que le destinataire existe
        recipient = supabase.table("utilisateurs")\
            .select("id, email, nom, prenom")\
            .eq("id", data.recipient_id)\
            .single()\
            .execute()
        
        if not recipient.data:
            raise HTTPException(status_code=404, detail="Destinataire non trouvé")
        
        # Vérifier qu'il existe un match entre les deux utilisateurs
        match_exists = supabase.table("matchings")\
            .select("id")\
            .or_(
                f"and(candidat_id.eq.{current_user['id']},recruteur_id.eq.{data.recipient_id}),"
                f"and(recruteur_id.eq.{current_user['id']},candidat_id.eq.{data.recipient_id})"
            )\
            .execute()
        
        if not match_exists.data:
            raise HTTPException(
                status_code=403, 
                detail="Vous devez avoir un match avec cet utilisateur pour lui envoyer un email"
            )
        
        # TODO: Intégrer service d'envoi d'email (SendGrid, Mailgun, etc.)
        # Pour l'instant, on simule l'envoi
        email_sent = {
            "to": recipient.data["email"],
            "from": current_user.get("email"),
            "subject": data.subject,
            "message": data.message,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        # Logger l'envoi
        supabase.table("email_logs").insert({
            "sender_id": current_user["id"],
            "recipient_id": data.recipient_id,
            "subject": data.subject,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }).execute()
        
        # Copier dans messagerie interne si demandé
        if data.copy_to_internal:
            supabase.table("messages").insert({
                "expediteur_id": current_user["id"],
                "destinataire_id": data.recipient_id,
                "contenu": f"**{data.subject}**\n\n{data.message}",
                "lu": False,
                "envoye_par_email": True
            }).execute()
            
            # Notification
            supabase.table("notifications").insert({
                "utilisateur_id": data.recipient_id,
                "type": "email",
                "titre": f"Email de {current_user.get('nom')}",
                "message": data.subject,
                "lu": False
            }).execute()
        
        logger.info(f"📧 Email envoyé: {current_user['id']} → {data.recipient_id}")
        
        return {
            "success": True,
            "message": "Email envoyé avec succès",
            "email": email_sent,
            "copied_to_internal": data.copy_to_internal
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/email/history")
async def get_email_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """📜 Historique de mes emails envoyés"""
    try:
        supabase = SupabaseService.get_client()
        
        result = supabase.table("email_logs")\
            .select("*")\
            .eq("sender_id", current_user["id"])\
            .order("sent_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {"emails": result.data or []}
    
    except Exception as e:
        logger.error(f"❌ Erreur historique emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== ENDPOINTS RENDEZ-VOUS =====

@router.post("/meetings")
async def schedule_meeting(
    data: ScheduleMeetingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    📅 Planifier un rendez-vous visio/téléphone.
    
    Génère un lien de visioconférence automatique (Zoom, Google Meet, etc.)
    et envoie les invitations par email.
    """
    try:
        supabase = SupabaseService.get_client()
        
        # Vérifier le destinataire
        recipient = supabase.table("utilisateurs")\
            .select("id, email, nom")\
            .eq("id", data.recipient_id)\
            .single()\
            .execute()
        
        if not recipient.data:
            raise HTTPException(status_code=404, detail="Destinataire non trouvé")
        
        # Vérifier le match
        match_exists = supabase.table("matchings")\
            .select("id")\
            .or_(
                f"and(candidat_id.eq.{current_user['id']},recruteur_id.eq.{data.recipient_id}),"
                f"and(recruteur_id.eq.{current_user['id']},candidat_id.eq.{data.recipient_id})"
            )\
            .execute()
        
        if not match_exists.data:
            raise HTTPException(
                status_code=403,
                detail="Vous devez avoir un match pour planifier un RDV"
            )
        
        # Générer un lien de visio unique
        meeting_id = str(uuid.uuid4())
        meeting_link = None
        
        if data.meeting_type == "video":
            # TODO: Intégrer Zoom/Google Meet/Jitsi API
            # Pour l'instant, on utilise un lien Jitsi simple
            meeting_link = f"https://meet.jit.si/recrut-der-{meeting_id}"
        
        # Créer le RDV
        meeting_data = {
            "organizer_id": current_user["id"],
            "participant_id": data.recipient_id,
            "title": data.title,
            "description": data.description,
            "scheduled_at": data.scheduled_at,
            "duration_minutes": data.duration_minutes,
            "meeting_type": data.meeting_type,
            "meeting_link": meeting_link,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("meetings").insert(meeting_data).execute()
        
        if result.data:
            meeting = result.data[0]
            
            # Notification au destinataire
            supabase.table("notifications").insert({
                "utilisateur_id": data.recipient_id,
                "type": "meeting_invitation",
                "titre": f"Invitation RDV de {current_user.get('nom')}",
                "message": f"{data.title} - {data.scheduled_at}",
                "lu": False,
                "metadata": {"meeting_id": meeting["id"]}
            }).execute()
            
            # TODO: Envoyer email d'invitation avec .ics
            
            logger.info(f"📅 RDV planifié: {meeting['id']}")
            
            return {
                "success": True,
                "meeting": meeting,
                "message": "Rendez-vous planifié avec succès"
            }
        
        raise HTTPException(status_code=500, detail="Erreur création RDV")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur planification RDV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/meetings")
async def get_my_meetings(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """📋 Liste de mes rendez-vous"""
    try:
        supabase = SupabaseService.get_client()
        
        query = supabase.table("meetings")\
            .select("*")\
            .or_(f"organizer_id.eq.{current_user['id']},participant_id.eq.{current_user['id']}")\
            .order("scheduled_at", desc=False)
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        
        return {"meetings": result.data or []}
    
    except Exception as e:
        logger.error(f"❌ Erreur liste RDV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/meetings/{meeting_id}")
async def get_meeting_detail(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """📅 Détail d'un rendez-vous"""
    try:
        supabase = SupabaseService.get_client()
        
        result = supabase.table("meetings")\
            .select("*")\
            .eq("id", meeting_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="RDV non trouvé")
        
        meeting = result.data
        
        # Vérifier que l'utilisateur est participant
        if meeting["organizer_id"] != current_user["id"] and meeting["participant_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        return meeting
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur détail RDV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/meetings/{meeting_id}")
async def update_meeting(
    meeting_id: str,
    data: UpdateMeetingRequest,
    current_user: dict = Depends(get_current_user)
):
    """✏️ Modifier un rendez-vous (confirmer, annuler, reporter)"""
    try:
        supabase = SupabaseService.get_client()
        
        # Récupérer le RDV
        meeting = supabase.table("meetings")\
            .select("*")\
            .eq("id", meeting_id)\
            .single()\
            .execute()
        
        if not meeting.data:
            raise HTTPException(status_code=404, detail="RDV non trouvé")
        
        # Vérifier les permissions
        if meeting.data["organizer_id"] != current_user["id"] and meeting.data["participant_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        # Construire les updates
        updates = {"updated_at": datetime.now().isoformat()}
        
        if data.status:
            updates["status"] = data.status
            
            # Si confirmé par le participant
            if data.status == "confirmed" and meeting.data["participant_id"] == current_user["id"]:
                updates["confirmed_at"] = datetime.now().isoformat()
        
        if data.scheduled_at:
            updates["scheduled_at"] = data.scheduled_at
            updates["status"] = "rescheduled"
        
        if data.notes:
            updates["notes"] = data.notes
        
        # Mettre à jour
        result = supabase.table("meetings")\
            .update(updates)\
            .eq("id", meeting_id)\
            .execute()
        
        # Notifier l'autre partie
        other_user_id = meeting.data["participant_id"] if current_user["id"] == meeting.data["organizer_id"] else meeting.data["organizer_id"]
        
        notification_messages = {
            "confirmed": "a confirmé le rendez-vous",
            "cancelled": "a annulé le rendez-vous",
            "rescheduled": "a reporté le rendez-vous",
            "completed": "a marqué le rendez-vous comme terminé"
        }
        
        if data.status and data.status in notification_messages:
            supabase.table("notifications").insert({
                "utilisateur_id": other_user_id,
                "type": "meeting_update",
                "titre": f"RDV: {current_user.get('nom')} {notification_messages[data.status]}",
                "message": meeting.data["title"],
                "lu": False
            }).execute()
        
        logger.info(f"✏️ RDV mis à jour: {meeting_id}")
        
        return {
            "success": True,
            "meeting": result.data[0] if result.data else {},
            "message": "Rendez-vous mis à jour"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur update RDV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """🗑️ Supprimer un rendez-vous"""
    try:
        supabase = SupabaseService.get_client()
        
        # Vérifier que c'est l'organisateur
        meeting = supabase.table("meetings")\
            .select("organizer_id, participant_id, title")\
            .eq("id", meeting_id)\
            .single()\
            .execute()
        
        if not meeting.data:
            raise HTTPException(status_code=404, detail="RDV non trouvé")
        
        if meeting.data["organizer_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Seul l'organisateur peut supprimer")
        
        # Notifier le participant
        supabase.table("notifications").insert({
            "utilisateur_id": meeting.data["participant_id"],
            "type": "meeting_cancelled",
            "titre": f"RDV annulé par {current_user.get('nom')}",
            "message": meeting.data["title"],
            "lu": False
        }).execute()
        
        # Supprimer
        supabase.table("meetings").delete().eq("id", meeting_id).execute()
        
        logger.info(f"🗑️ RDV supprimé: {meeting_id}")
        
        return {"success": True, "message": "Rendez-vous supprimé"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression RDV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
