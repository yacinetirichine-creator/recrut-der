"""
📦 Recrut'der - Modèles Pydantic pour nouvelles tables V2
==========================================================
Entreprises, Swipes, Messages, Notifications, RGPD, Support
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# ============================================================
# ENTREPRISES
# ============================================================

class TailleEntreprise(str, Enum):
    STARTUP = "startup"
    PME = "pme"
    ETI = "eti"
    GRAND_GROUPE = "grand_groupe"


class NombreEmployes(str, Enum):
    UN_DIX = "1-10"
    ONZE_CINQUANTE = "11-50"
    CINQUANTE_DEUX_CENTS = "51-200"
    DEUX_CENTS_CINQ_CENTS = "201-500"
    PLUS_CINQ_CENTS = "500+"


class EntrepriseBase(BaseModel):
    nom: str
    siret: Optional[str] = None
    siren: Optional[str] = None
    forme_juridique: Optional[str] = None
    description: Optional[str] = None
    secteur: Optional[str] = None
    taille_entreprise: Optional[TailleEntreprise] = None
    nombre_employes: Optional[NombreEmployes] = None
    siege_social: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: str = "France"
    site_web: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None


class EntrepriseCreate(EntrepriseBase):
    pass


class EntrepriseUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    secteur: Optional[str] = None
    taille_entreprise: Optional[TailleEntreprise] = None
    nombre_employes: Optional[NombreEmployes] = None
    site_web: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None


class EntrepriseResponse(EntrepriseBase):
    id: UUID
    verified: bool = False
    verified_at: Optional[datetime] = None
    actif: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# SWIPES (Type Tinder)
# ============================================================

class SwipeAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SUPER_LIKE = "super_like"


class SwipeType(str, Enum):
    CANDIDAT_TO_OFFRE = "candidat_to_offre"
    RECRUTEUR_TO_CANDIDAT = "recruteur_to_candidat"


class SwipeCreate(BaseModel):
    type_swipe: SwipeType
    action: SwipeAction
    candidat_id: Optional[UUID] = None
    offre_id: Optional[UUID] = None


class SwipeResponse(BaseModel):
    id: UUID
    user_id: UUID
    type_swipe: SwipeType
    action: SwipeAction
    candidat_id: Optional[UUID] = None
    offre_id: Optional[UUID] = None
    is_match: bool = False
    matched_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CONVERSATIONS & MESSAGES
# ============================================================

class ConversationResponse(BaseModel):
    id: UUID
    candidat_id: UUID
    recruteur_id: UUID
    offre_id: Optional[UUID] = None
    match_id: UUID
    actif: bool = True
    archived_by_candidat: bool = False
    archived_by_recruteur: bool = False
    last_message_at: datetime
    last_message_preview: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    conversation_id: UUID
    contenu: str
    attachments: Optional[List[Dict[str, Any]]] = []


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    contenu: str
    attachments: Optional[List[Dict[str, Any]]] = []
    lu: bool = False
    lu_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationType(str, Enum):
    NEW_MATCH = "new_match"
    NEW_MESSAGE = "new_message"
    CANDIDATURE_VUE = "candidature_vue"
    PROFILE_VUE = "profile_vue"
    SUPER_LIKE_RECU = "super_like_recu"
    OFFRE_EXPIRING = "offre_expiring"
    SYSTEM = "system"


class NotificationCreate(BaseModel):
    user_id: UUID
    type: NotificationType
    titre: str
    message: str
    link_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: NotificationType
    titre: str
    message: str
    link_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}
    lu: bool = False
    lu_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ADMIN LOGS
# ============================================================

class AdminActionType(str, Enum):
    USER_SUSPENDED = "user_suspended"
    USER_BANNED = "user_banned"
    USER_VERIFIED = "user_verified"
    OFFRE_MODERATED = "offre_moderated"
    CONTENT_DELETED = "content_deleted"
    SETTINGS_CHANGED = "settings_changed"
    SUPPORT_TICKET_RESOLVED = "support_ticket_resolved"
    RGPD_REQUEST_PROCESSED = "rgpd_request_processed"


class AdminLogCreate(BaseModel):
    action: AdminActionType
    description: str
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = {}


class AdminLogResponse(BaseModel):
    id: UUID
    admin_id: Optional[UUID] = None
    admin_email: str
    action: AdminActionType
    description: str
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = {}
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# RGPD - CONSENTEMENTS
# ============================================================

class ConsentType(str, Enum):
    COOKIES_ESSENTIAL = "cookies_essential"
    COOKIES_ANALYTICS = "cookies_analytics"
    COOKIES_MARKETING = "cookies_marketing"
    DATA_PROCESSING = "data_processing"
    MARKETING_EMAILS = "marketing_emails"
    MARKETING_SMS = "marketing_sms"


class RGPDConsentCreate(BaseModel):
    consent_type: ConsentType
    consented: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RGPDConsentResponse(BaseModel):
    id: UUID
    user_id: UUID
    consent_type: ConsentType
    consented: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# RGPD - DEMANDES
# ============================================================

class RGPDRequestType(str, Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    DELETION = "deletion"
    PORTABILITY = "portability"
    OPPOSITION = "opposition"


class RGPDRequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class RGPDRequestCreate(BaseModel):
    request_type: RGPDRequestType
    description: Optional[str] = None


class RGPDRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    request_type: RGPDRequestType
    status: RGPDRequestStatus
    description: Optional[str] = None
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    response: Optional[str] = None
    export_file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# FAQ
# ============================================================

class FAQCategory(str, Enum):
    COMPTE = "compte"
    CANDIDAT = "candidat"
    RECRUTEUR = "recruteur"
    MATCHING = "matching"
    MESSAGERIE = "messagerie"
    PAIEMENT = "paiement"
    RGPD = "rgpd"
    TECHNIQUE = "technique"


class FAQCreate(BaseModel):
    category: FAQCategory
    question: str
    reponse: str
    slug: Optional[str] = None
    published: bool = True
    ordre: int = 0


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    reponse: Optional[str] = None
    published: Optional[bool] = None
    ordre: Optional[int] = None


class FAQResponse(BaseModel):
    id: UUID
    category: FAQCategory
    question: str
    reponse: str
    slug: Optional[str] = None
    vues: int = 0
    utile_count: int = 0
    published: bool = True
    ordre: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# SUPPORT TICKETS
# ============================================================

class TicketCategory(str, Enum):
    TECHNIQUE = "technique"
    COMPTE = "compte"
    PAIEMENT = "paiement"
    ABUS = "abus"
    RGPD = "rgpd"
    AUTRE = "autre"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicketCreate(BaseModel):
    sujet: str
    message: str
    category: TicketCategory
    priority: Optional[TicketPriority] = TicketPriority.MEDIUM
    attachments: Optional[List[Dict[str, Any]]] = []


class SupportTicketResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    user_email: str
    user_name: Optional[str] = None
    sujet: str
    message: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    assigned_to: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketMessageCreate(BaseModel):
    ticket_id: UUID
    message: str
    attachments: Optional[List[Dict[str, Any]]] = []


class SupportTicketMessageResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    sender_id: Optional[UUID] = None
    sender_email: str
    is_admin: bool = False
    message: str
    attachments: Optional[List[Dict[str, Any]]] = []
    created_at: datetime

    class Config:
        from_attributes = True
