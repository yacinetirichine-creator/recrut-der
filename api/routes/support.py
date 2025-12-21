"""
🎫 Routes Support & Chatbot IA
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger
from datetime import datetime

from ..database.supabase_client import SupabaseService
from .auth import get_current_user


router = APIRouter()


# ===== MODÈLES PYDANTIC =====

class ChatMessage(BaseModel):
    """Message pour le chatbot"""
    message: str = Field(..., description="Message de l'utilisateur")
    conversation_id: Optional[str] = Field(None, description="ID de conversation pour contexte")


class ChatResponse(BaseModel):
    """Réponse du chatbot"""
    response: str
    needs_ticket: bool = False
    suggested_faqs: List[dict] = []
    conversation_id: str
    confidence: float = 0.0


class CreateTicketRequest(BaseModel):
    """Création de ticket support"""
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10)
    priority: str = Field("normale", pattern="^(basse|normale|haute|urgente)$")
    conversation_id: Optional[str] = None


class TicketMessageRequest(BaseModel):
    """Ajout de message à un ticket"""
    message: str = Field(..., min_length=1)


class FAQSearchRequest(BaseModel):
    """Recherche FAQ"""
    query: str = Field(..., min_length=2)
    category: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


# ===== ENDPOINTS CHATBOT =====

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    data: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    💬 Discuter avec le chatbot IA.
    
    Le chatbot peut:
    - Répondre aux questions
    - Suggérer des FAQ
    - Créer des tickets si nécessaire
    """
    try:
        from ..services.chatbot_service import ChatbotService
        
        chatbot = ChatbotService()
        supabase = SupabaseService.get_client()
        
        # Récupérer l'historique de conversation si fourni
        conversation_history = []
        conversation_id = data.conversation_id
        
        if conversation_id:
            # Charger l'historique
            history_result = supabase.table("chatbot_conversations")\
                .select("messages")\
                .eq("id", conversation_id)\
                .eq("user_id", current_user["id"])\
                .single()\
                .execute()
            
            if history_result.data:
                conversation_history = history_result.data.get("messages", [])
        else:
            # Créer nouvelle conversation
            conv_data = {
                "user_id": current_user["id"],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
            conv_result = supabase.table("chatbot_conversations").insert(conv_data).execute()
            if conv_result.data:
                conversation_id = conv_result.data[0]["id"]
        
        # Contexte utilisateur
        user_context = {
            "type": "candidat" if current_user.get("type") == "candidat" else "recruteur",
            "name": current_user.get("nom")
        }
        
        # Générer la réponse
        response = await chatbot.chat(
            message=data.message,
            conversation_history=conversation_history,
            user_context=user_context
        )
        
        # Mettre à jour l'historique
        conversation_history.append({"role": "user", "content": data.message})
        conversation_history.append({"role": "assistant", "content": response["response"]})
        
        if conversation_id:
            supabase.table("chatbot_conversations")\
                .update({
                    "messages": conversation_history,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", conversation_id)\
                .execute()
        
        # Suggérer des FAQ si pertinent
        suggested_faqs = []
        if response.get("needs_ticket"):
            suggested_faqs = await chatbot.get_faq_suggestions(data.message, limit=3)
        
        return ChatResponse(
            response=response["response"],
            needs_ticket=response.get("needs_ticket", False),
            suggested_faqs=suggested_faqs,
            conversation_id=conversation_id,
            confidence=response.get("confidence", 0.0)
        )
    
    except Exception as e:
        logger.error(f"Erreur chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur chatbot: {str(e)}"
        )


# ===== ENDPOINTS FAQ =====

@router.post("/faq/search")
async def search_faq(data: FAQSearchRequest):
    """
    🔍 Rechercher dans la FAQ.
    
    Recherche intelligente dans les questions fréquentes.
    """
    try:
        supabase = SupabaseService.get_client()
        
        # Base query
        query = supabase.table("faq_questions").select("*").eq("published", True)
        
        # Filtrer par catégorie si fourni
        if data.category:
            query = query.eq("category", data.category)
        
        # Exécuter
        result = query.limit(data.limit).execute()
        
        if not result.data:
            return {"results": [], "total": 0}
        
        # Filtrer par pertinence simple
        query_words = set(data.query.lower().split())
        scored_results = []
        
        for faq in result.data:
            question_words = set(faq["question"].lower().split())
            answer_words = set(faq.get("answer", "").lower().split())
            
            q_score = len(query_words.intersection(question_words)) * 2
            a_score = len(query_words.intersection(answer_words))
            total_score = q_score + a_score
            
            if total_score > 0:
                scored_results.append({
                    **faq,
                    "relevance_score": total_score
                })
        
        # Trier par pertinence
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "results": scored_results[:data.limit],
            "total": len(scored_results)
        }
    
    except Exception as e:
        logger.error(f"Erreur search_faq: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/faq/categories")
async def get_faq_categories():
    """📂 Liste des catégories FAQ"""
    try:
        supabase = SupabaseService.get_client()
        
        # Récupérer toutes les catégories distinctes
        result = supabase.table("faq_questions")\
            .select("category")\
            .eq("published", True)\
            .execute()
        
        if result.data:
            categories = list(set(item["category"] for item in result.data if item.get("category")))
            
            # Compter les questions par catégorie
            category_counts = {}
            for cat in categories:
                count_result = supabase.table("faq_questions")\
                    .select("id", count="exact")\
                    .eq("category", cat)\
                    .eq("published", True)\
                    .execute()
                
                category_counts[cat] = count_result.count or 0
            
            return {
                "categories": [
                    {"name": cat, "count": category_counts.get(cat, 0)}
                    for cat in sorted(categories)
                ]
            }
        
        return {"categories": []}
    
    except Exception as e:
        logger.error(f"Erreur get_faq_categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/faq/popular")
async def get_popular_faq(limit: int = 10):
    """⭐ Questions FAQ les plus consultées"""
    try:
        supabase = SupabaseService.get_client()
        
        result = supabase.table("faq_questions")\
            .select("*")\
            .eq("published", True)\
            .order("views", desc=True)\
            .limit(limit)\
            .execute()
        
        return {"faqs": result.data or []}
    
    except Exception as e:
        logger.error(f"Erreur get_popular_faq: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/faq/{faq_id}/view")
async def increment_faq_view(faq_id: str):
    """👁️ Incrémenter le compteur de vues d'une FAQ"""
    try:
        supabase = SupabaseService.get_client()
        
        # Récupérer la FAQ
        faq_result = supabase.table("faq_questions").select("views").eq("id", faq_id).single().execute()
        
        if not faq_result.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")
        
        current_views = faq_result.data.get("views", 0)
        
        # Incrémenter
        supabase.table("faq_questions")\
            .update({"views": current_views + 1})\
            .eq("id", faq_id)\
            .execute()
        
        return {"success": True, "views": current_views + 1}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur increment_faq_view: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== ENDPOINTS TICKETS SUPPORT =====

@router.post("/tickets")
async def create_support_ticket(
    data: CreateTicketRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🎫 Créer un ticket de support.
    
    Peut être créé depuis le chatbot ou directement.
    """
    try:
        from ..services.chatbot_service import ChatbotService
        
        # Récupérer le contexte de conversation si fourni
        conversation_context = None
        if data.conversation_id:
            supabase = SupabaseService.get_client()
            conv_result = supabase.table("chatbot_conversations")\
                .select("messages")\
                .eq("id", data.conversation_id)\
                .eq("user_id", current_user["id"])\
                .single()\
                .execute()
            
            if conv_result.data:
                conversation_context = conv_result.data.get("messages", [])
        
        # Créer le ticket
        chatbot = ChatbotService()
        result = await chatbot.create_support_ticket(
            user_id=current_user["id"],
            subject=data.subject,
            message=data.message,
            priority=data.priority,
            conversation_context=conversation_context
        )
        
        if result.get("success"):
            return result["ticket"]
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Erreur création ticket")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur create_support_ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tickets")
async def get_my_tickets(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """📋 Liste de mes tickets support"""
    try:
        supabase = SupabaseService.get_client()
        
        query = supabase.table("support_tickets")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        
        return {"tickets": result.data or []}
    
    except Exception as e:
        logger.error(f"Erreur get_my_tickets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    """🎫 Détail d'un ticket avec messages"""
    try:
        supabase = SupabaseService.get_client()
        
        # Récupérer le ticket
        ticket_result = supabase.table("support_tickets")\
            .select("*")\
            .eq("id", ticket_id)\
            .single()\
            .execute()
        
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
        ticket = ticket_result.data
        
        # Vérifier que c'est bien le ticket de l'utilisateur
        if ticket["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        # Récupérer les messages
        messages_result = supabase.table("support_ticket_messages")\
            .select("*")\
            .eq("ticket_id", ticket_id)\
            .order("created_at", desc=False)\
            .execute()
        
        ticket["messages"] = messages_result.data or []
        
        return ticket
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_ticket_detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/tickets/{ticket_id}/messages")
async def add_ticket_message(
    ticket_id: str,
    data: TicketMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """💬 Ajouter un message à un ticket"""
    try:
        supabase = SupabaseService.get_client()
        
        # Vérifier que le ticket existe et appartient à l'utilisateur
        ticket_result = supabase.table("support_tickets")\
            .select("user_id, status")\
            .eq("id", ticket_id)\
            .single()\
            .execute()
        
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
        if ticket_result.data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        if ticket_result.data["status"] in ["resolved", "closed"]:
            raise HTTPException(status_code=400, detail="Ticket fermé")
        
        # Créer le message
        message_data = {
            "ticket_id": ticket_id,
            "user_id": current_user["id"],
            "message": data.message,
            "is_staff": False,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("support_ticket_messages").insert(message_data).execute()
        
        # Mettre à jour le statut du ticket si nécessaire
        if ticket_result.data["status"] == "waiting_user":
            supabase.table("support_tickets")\
                .update({"status": "in_progress"})\
                .eq("id", ticket_id)\
                .execute()
        
        return result.data[0] if result.data else {}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur add_ticket_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    """🔒 Fermer un ticket (utilisateur)"""
    try:
        supabase = SupabaseService.get_client()
        
        # Vérifier que le ticket existe et appartient à l'utilisateur
        ticket_result = supabase.table("support_tickets")\
            .select("user_id")\
            .eq("id", ticket_id)\
            .single()\
            .execute()
        
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
        if ticket_result.data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        # Fermer le ticket
        result = supabase.table("support_tickets")\
            .update({"status": "closed", "closed_at": datetime.now().isoformat()})\
            .eq("id", ticket_id)\
            .execute()
        
        return {"success": True, "ticket": result.data[0] if result.data else {}}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur close_ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
