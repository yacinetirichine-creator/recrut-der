"""
🔔 Recrut'der - Routes Notifications
=====================================
Gestion des notifications utilisateur
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID

from api.models.v2_models import NotificationResponse
from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from loguru import logger


router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: dict = Depends(get_current_user),
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """
    🔔 Récupérer mes notifications
    
    - unread_only=true : Uniquement les non lues
    - unread_only=false : Toutes les notifications
    """
    try:
        query = supabase.table("notifications")\
            .select("*")\
            .eq("user_id", current_user["id"])
        
        if unread_only:
            query = query.eq("lu", False)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Marquer une notification comme lue
    """
    try:
        result = supabase.table("notifications")\
            .update({"lu": True, "lu_at": "NOW()"})\
            .eq("id", str(notification_id))\
            .eq("user_id", current_user["id"])\
            .execute()
        
        logger.info(f"✅ Notification {notification_id} marquée comme lue")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erreur marquage notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/mark-all-read")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """
    ✅ Marquer toutes mes notifications comme lues
    """
    try:
        result = supabase.table("notifications")\
            .update({"lu": True, "lu_at": "NOW()"})\
            .eq("user_id", current_user["id"])\
            .eq("lu", False)\
            .execute()
        
        logger.info(f"✅ Toutes les notifications marquées comme lues pour {current_user['email']}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erreur marquage toutes notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/unread-count")
async def get_unread_notifications_count(current_user: dict = Depends(get_current_user)):
    """
    🔢 Compter le nombre de notifications non lues
    """
    try:
        result = supabase.table("notifications")\
            .select("*", count="exact")\
            .eq("user_id", current_user["id"])\
            .eq("lu", False)\
            .execute()
        
        return {"count": result.count}
        
    except Exception as e:
        logger.error(f"❌ Erreur comptage notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    🗑️ Supprimer une notification
    """
    try:
        result = supabase.table("notifications")\
            .delete()\
            .eq("id", str(notification_id))\
            .eq("user_id", current_user["id"])\
            .execute()
        
        logger.info(f"✅ Notification {notification_id} supprimée")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
