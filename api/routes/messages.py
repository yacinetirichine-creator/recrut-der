"""
💬 Recrut'der - Routes Messagerie
==================================
Conversations et messages entre candidats et recruteurs matchés
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID

from api.models.v2_models import (
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from loguru import logger


router = APIRouter()


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_my_conversations(
    current_user: dict = Depends(get_current_user),
    archived: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """
    💬 Récupérer mes conversations
    
    - archived=false : Conversations actives
    - archived=true : Conversations archivées
    """
    try:
        # Récupérer le profil (candidat ou recruteur)
        candidat = supabase.table("candidats")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        recruteur = supabase.table("recruteurs")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        query = supabase.table("conversations").select("*")
        
        if candidat.data:
            # Utilisateur est candidat
            candidat_id = candidat.data[0]["id"]
            query = query.eq("candidat_id", candidat_id)
            if archived:
                query = query.eq("archived_by_candidat", True)
            else:
                query = query.eq("archived_by_candidat", False)
                
        elif recruteur.data:
            # Utilisateur est recruteur
            recruteur_id = recruteur.data[0]["id"]
            query = query.eq("recruteur_id", recruteur_id)
            if archived:
                query = query.eq("archived_by_recruteur", True)
            else:
                query = query.eq("archived_by_recruteur", False)
        else:
            return []
        
        result = query.eq("actif", True)\
            .order("last_message_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    📄 Récupérer une conversation spécifique
    """
    try:
        result = supabase.table("conversations")\
            .select("*")\
            .eq("id", str(conversation_id))\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation non trouvée"
            )
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    📨 Récupérer les messages d'une conversation
    """
    try:
        result = supabase.table("messages")\
            .select("*")\
            .eq("conversation_id", str(conversation_id))\
            .order("created_at", desc=False)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    📤 Envoyer un message dans une conversation
    
    Le trigger SQL mettra automatiquement à jour la conversation
    et créera une notification pour le destinataire.
    """
    try:
        # Créer le message
        message_insert = {
            "conversation_id": str(message_data.conversation_id),
            "sender_id": current_user["id"],
            "contenu": message_data.contenu,
            "attachments": message_data.attachments or []
        }
        
        result = supabase.table("messages")\
            .insert(message_insert)\
            .execute()
        
        message = result.data[0]
        
        logger.info(f"✅ Message envoyé dans conversation {message_data.conversation_id}")
        
        return message
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/messages/{message_id}/mark-read")
async def mark_message_as_read(
    message_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Marquer un message comme lu
    """
    try:
        result = supabase.table("messages")\
            .update({"lu": True, "lu_at": "NOW()"})\
            .eq("id", str(message_id))\
            .execute()
        
        logger.info(f"✅ Message {message_id} marqué comme lu")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erreur marquage message lu: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    🗄️ Archiver une conversation
    """
    try:
        # Déterminer si l'utilisateur est candidat ou recruteur
        candidat = supabase.table("candidats")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        recruteur = supabase.table("recruteurs")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if candidat.data:
            field = "archived_by_candidat"
        elif recruteur.data:
            field = "archived_by_recruteur"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utilisateur non autorisé"
            )
        
        result = supabase.table("conversations")\
            .update({field: True})\
            .eq("id", str(conversation_id))\
            .execute()
        
        logger.info(f"✅ Conversation {conversation_id} archivée")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erreur archivage conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/unread-count")
async def get_unread_messages_count(current_user: dict = Depends(get_current_user)):
    """
    🔔 Compter le nombre de messages non lus
    """
    try:
        # Récupérer toutes mes conversations
        candidat = supabase.table("candidats")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        recruteur = supabase.table("recruteurs")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if candidat.data:
            conversations = supabase.table("conversations")\
                .select("id")\
                .eq("candidat_id", candidat.data[0]["id"])\
                .execute()
        elif recruteur.data:
            conversations = supabase.table("conversations")\
                .select("id")\
                .eq("recruteur_id", recruteur.data[0]["id"])\
                .execute()
        else:
            return {"count": 0}
        
        conversation_ids = [c["id"] for c in conversations.data]
        
        if not conversation_ids:
            return {"count": 0}
        
        # Compter les messages non lus dans ces conversations
        result = supabase.table("messages")\
            .select("*", count="exact")\
            .in_("conversation_id", conversation_ids)\
            .eq("lu", False)\
            .neq("sender_id", current_user["id"])\
            .execute()
        
        return {"count": result.count}
        
    except Exception as e:
        logger.error(f"❌ Erreur comptage messages non lus: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
