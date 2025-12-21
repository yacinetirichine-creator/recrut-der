"""
🤖 Service Chatbot IA pour support utilisateur
"""

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from ..config import settings
from ..database.supabase_client import SupabaseService


class ChatbotService:
    """Service de chatbot IA pour le support"""
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER if hasattr(settings, 'AI_PROVIDER') else "openai"
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                logger.warning("OPENAI_API_KEY non configuré")
                self.client = None
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
                self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            else:
                logger.warning("ANTHROPIC_API_KEY non configuré")
                self.client = None
        else:
            logger.warning(f"Provider {self.provider} non disponible ou non configuré")
            self.client = None
    
    
    def get_system_prompt(self) -> str:
        """Prompt système pour le chatbot"""
        return """Tu es un assistant virtuel intelligent pour Recrut'der, une plateforme de matching entre candidats et recruteurs type Tinder.

Ton rôle:
- Aider les utilisateurs (candidats et recruteurs) à utiliser la plateforme
- Répondre aux questions fréquentes
- Créer des tickets de support si nécessaire
- Être courtois, professionnel et efficace

Fonctionnalités principales de Recrut'der:
- Swipe type Tinder sur profils/offres
- Matching intelligent avec IA
- CV parsing automatique
- Messagerie entre matchs
- Dashboard recruteur avec multi-publication d'offres

Règles importantes:
- Si tu ne connais pas la réponse, dis-le et propose de créer un ticket support
- Reste concis (max 3-4 phrases)
- Utilise un ton amical mais professionnel
- Propose des solutions concrètes
"""
    
    
    async def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        user_context: Dict = None
    ) -> Dict:
        """
        Générer une réponse du chatbot.
        
        Args:
            message: Message de l'utilisateur
            conversation_history: Historique de la conversation
            user_context: Contexte utilisateur (type, nom, etc.)
            
        Returns:
            Dict avec la réponse et des métadonnées
        """
        if not self.client:
            return {
                "response": "Désolé, le chatbot IA n'est pas disponible actuellement. Veuillez créer un ticket de support.",
                "needs_ticket": True,
                "confidence": 0
            }
        
        try:
            # Construire l'historique
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            
            # Ajouter le contexte utilisateur
            if user_context:
                context_msg = f"Contexte utilisateur: Type={user_context.get('type', 'inconnu')}"
                if user_context.get('name'):
                    context_msg += f", Nom={user_context['name']}"
                messages.append({"role": "system", "content": context_msg})
            
            # Ajouter l'historique
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Garder les 10 derniers messages
            
            # Ajouter le message actuel
            messages.append({"role": "user", "content": message})
            
            # Générer la réponse selon le provider
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                
            elif self.provider == "anthropic":
                # Anthropic nécessite un format différent
                system_prompt = self.get_system_prompt()
                if user_context:
                    system_prompt += f"\n\nContexte utilisateur: Type={user_context.get('type', 'inconnu')}"
                
                # Convertir l'historique
                formatted_messages = []
                for msg in (conversation_history or [])[-10:]:
                    if msg["role"] != "system":
                        formatted_messages.append(msg)
                formatted_messages.append({"role": "user", "content": message})
                
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=300,
                    system=system_prompt,
                    messages=formatted_messages
                )
                
                ai_response = response.content[0].text
            
            else:
                return {
                    "response": "Provider IA non supporté.",
                    "needs_ticket": True,
                    "confidence": 0
                }
            
            # Analyser si un ticket est nécessaire
            needs_ticket = self._should_create_ticket(message, ai_response)
            
            return {
                "response": ai_response,
                "needs_ticket": needs_ticket,
                "confidence": 0.8,
                "provider": self.provider
            }
        
        except Exception as e:
            logger.error(f"Erreur chatbot: {str(e)}")
            return {
                "response": "Désolé, une erreur s'est produite. Voulez-vous créer un ticket de support ?",
                "needs_ticket": True,
                "confidence": 0,
                "error": str(e)
            }
    
    
    def _should_create_ticket(self, user_message: str, ai_response: str) -> bool:
        """Déterminer si un ticket support doit être créé"""
        # Mots-clés indiquant un problème technique
        technical_keywords = [
            "bug", "erreur", "ne fonctionne pas", "cassé", "problème technique",
            "bloqué", "crash", "ne marche pas", "impossible de"
        ]
        
        # Phrases du bot indiquant qu'il ne peut pas aider
        bot_cant_help = [
            "je ne sais pas", "je ne peux pas", "créer un ticket",
            "contacter le support", "équipe support"
        ]
        
        message_lower = user_message.lower()
        response_lower = ai_response.lower()
        
        # Si le message contient des mots-clés techniques
        if any(keyword in message_lower for keyword in technical_keywords):
            return True
        
        # Si le bot dit qu'il ne peut pas aider
        if any(phrase in response_lower for phrase in bot_cant_help):
            return True
        
        return False
    
    
    async def get_faq_suggestions(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Trouver des questions FAQ pertinentes.
        
        Args:
            query: Recherche utilisateur
            limit: Nombre de résultats
            
        Returns:
            Liste de questions FAQ
        """
        try:
            supabase = SupabaseService.get_client()
            
            # Recherche simple (peut être amélioré avec full-text search)
            result = supabase.table("faq_questions").select("*").eq("published", True).limit(limit).execute()
            
            if result.data:
                # Filtrer par pertinence (simple matching de mots-clés)
                query_words = set(query.lower().split())
                
                scored_faqs = []
                for faq in result.data:
                    question_words = set(faq["question"].lower().split())
                    answer_words = set(faq["answer"].lower().split())
                    
                    # Score basé sur les mots communs
                    question_score = len(query_words.intersection(question_words))
                    answer_score = len(query_words.intersection(answer_words)) * 0.5
                    total_score = question_score + answer_score
                    
                    if total_score > 0:
                        scored_faqs.append({
                            **faq,
                            "relevance_score": total_score
                        })
                
                # Trier par pertinence
                scored_faqs.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                return scored_faqs[:limit]
            
            return []
        
        except Exception as e:
            logger.error(f"Erreur get_faq_suggestions: {str(e)}")
            return []
    
    
    async def create_support_ticket(
        self,
        user_id: str,
        subject: str,
        message: str,
        priority: str = "normale",
        conversation_context: List[Dict] = None
    ) -> Dict:
        """
        Créer un ticket de support.
        
        Args:
            user_id: ID de l'utilisateur
            subject: Sujet du ticket
            message: Message initial
            priority: Priorité (basse, normale, haute, urgente)
            conversation_context: Contexte de la conversation avec le chatbot
            
        Returns:
            Ticket créé
        """
        try:
            supabase = SupabaseService.get_client()
            
            # Créer le ticket
            ticket_data = {
                "user_id": user_id,
                "subject": subject,
                "description": message,
                "priority": priority,
                "status": "open",
                "created_at": datetime.now().isoformat()
            }
            
            # Ajouter le contexte chatbot si disponible
            if conversation_context:
                ticket_data["metadata"] = {
                    "chatbot_conversation": conversation_context[-5:]  # Derniers 5 messages
                }
            
            result = supabase.table("support_tickets").insert(ticket_data).execute()
            
            if result.data:
                ticket = result.data[0]
                
                # Créer le premier message
                message_data = {
                    "ticket_id": ticket["id"],
                    "user_id": user_id,
                    "message": message,
                    "is_staff": False,
                    "created_at": datetime.now().isoformat()
                }
                
                supabase.table("support_ticket_messages").insert(message_data).execute()
                
                logger.info(f"Ticket créé: {ticket['id']}")
                
                return {
                    "success": True,
                    "ticket": ticket
                }
            
            return {
                "success": False,
                "error": "Impossible de créer le ticket"
            }
        
        except Exception as e:
            logger.error(f"Erreur create_support_ticket: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
