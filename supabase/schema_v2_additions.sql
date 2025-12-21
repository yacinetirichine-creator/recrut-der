-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  RECRUT'DER V2 - NOUVELLES TABLES                            ║
-- ║  Phase 1: Architecture complète type "Tinder du recrutement" ║
-- ╚═══════════════════════════════════════════════════════════════╝

-- ============================================================
-- 1. TABLE ENTREPRISES (séparée des recruteurs)
-- ============================================================

CREATE TABLE public.entreprises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Informations légales
    nom TEXT NOT NULL,
    siret TEXT UNIQUE,
    siren TEXT,
    forme_juridique TEXT,
    
    -- Description
    description TEXT,
    secteur TEXT,
    taille_entreprise TEXT, -- 'startup', 'pme', 'eti', 'grand_groupe'
    nombre_employes TEXT, -- '1-10', '11-50', '51-200', '201-500', '500+'
    
    -- Localisation
    siege_social TEXT,
    ville TEXT,
    code_postal TEXT,
    pays TEXT DEFAULT 'France',
    
    -- Contact & Web
    site_web TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    
    -- Visuels
    logo_url TEXT,
    cover_image_url TEXT,
    
    -- Vérification
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    actif BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_entreprises_siret ON public.entreprises(siret);
CREATE INDEX idx_entreprises_nom ON public.entreprises(nom);
CREATE INDEX idx_entreprises_verified ON public.entreprises(verified);

-- ============================================================
-- 2. MODIFIER TABLE RECRUTEURS (lier à entreprise)
-- ============================================================

ALTER TABLE public.recruteurs 
ADD COLUMN IF NOT EXISTS entreprise_id UUID REFERENCES public.entreprises(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_recruteurs_entreprise ON public.recruteurs(entreprise_id);

-- ============================================================
-- 3. TABLE SWIPES (Like/Dislike type Tinder)
-- ============================================================

CREATE TYPE swipe_action AS ENUM ('like', 'dislike', 'super_like');
CREATE TYPE swipe_type AS ENUM ('candidat_to_offre', 'recruteur_to_candidat');

CREATE TABLE public.swipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Qui swipe
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Type de swipe
    type_swipe swipe_type NOT NULL,
    action swipe_action NOT NULL,
    
    -- Vers qui/quoi
    candidat_id UUID REFERENCES public.candidats(id) ON DELETE CASCADE,
    offre_id UUID REFERENCES public.offres(id) ON DELETE CASCADE,
    
    -- Match automatique si les 2 ont like
    is_match BOOLEAN DEFAULT false,
    matched_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contrainte : un user ne peut swiper qu'une fois sur une même cible
    UNIQUE(user_id, candidat_id, offre_id)
);

-- Index pour recherche rapide
CREATE INDEX idx_swipes_user ON public.swipes(user_id);
CREATE INDEX idx_swipes_candidat ON public.swipes(candidat_id);
CREATE INDEX idx_swipes_offre ON public.swipes(offre_id);
CREATE INDEX idx_swipes_match ON public.swipes(is_match);
CREATE INDEX idx_swipes_created ON public.swipes(created_at DESC);

-- ============================================================
-- 4. TABLE CONVERSATIONS (Messagerie)
-- ============================================================

CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Participants (candidat + recruteur)
    candidat_id UUID REFERENCES public.candidats(id) ON DELETE CASCADE,
    recruteur_id UUID REFERENCES public.recruteurs(id) ON DELETE CASCADE,
    offre_id UUID REFERENCES public.offres(id) ON DELETE SET NULL,
    
    -- Match associé
    match_id UUID REFERENCES public.swipes(id) ON DELETE CASCADE,
    
    -- Statut
    actif BOOLEAN DEFAULT true,
    archived_by_candidat BOOLEAN DEFAULT false,
    archived_by_recruteur BOOLEAN DEFAULT false,
    
    -- Dernier message
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_preview TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(candidat_id, recruteur_id, offre_id)
);

-- Index
CREATE INDEX idx_conversations_candidat ON public.conversations(candidat_id);
CREATE INDEX idx_conversations_recruteur ON public.conversations(recruteur_id);
CREATE INDEX idx_conversations_offre ON public.conversations(offre_id);
CREATE INDEX idx_conversations_last_message ON public.conversations(last_message_at DESC);

-- ============================================================
-- 5. TABLE MESSAGES (Messages dans conversations)
-- ============================================================

CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    
    -- Expéditeur
    sender_id UUID REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Contenu
    contenu TEXT NOT NULL,
    
    -- Pièces jointes
    attachments JSONB DEFAULT '[]',
    
    -- Statut
    lu BOOLEAN DEFAULT false,
    lu_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_messages_conversation ON public.messages(conversation_id);
CREATE INDEX idx_messages_sender ON public.messages(sender_id);
CREATE INDEX idx_messages_created ON public.messages(created_at DESC);
CREATE INDEX idx_messages_lu ON public.messages(lu);

-- ============================================================
-- 6. TABLE NOTIFICATIONS
-- ============================================================

CREATE TYPE notification_type AS ENUM (
    'new_match',
    'new_message',
    'candidature_vue',
    'profile_vue',
    'super_like_recu',
    'offre_expiring',
    'system'
);

CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Destinataire
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Type & Contenu
    type notification_type NOT NULL,
    titre TEXT NOT NULL,
    message TEXT NOT NULL,
    
    -- Lien associé
    link_url TEXT,
    
    -- Données JSON pour contexte additionnel
    data JSONB DEFAULT '{}',
    
    -- Statut
    lu BOOLEAN DEFAULT false,
    lu_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_notifications_user ON public.notifications(user_id);
CREATE INDEX idx_notifications_lu ON public.notifications(lu);
CREATE INDEX idx_notifications_created ON public.notifications(created_at DESC);
CREATE INDEX idx_notifications_type ON public.notifications(type);

-- ============================================================
-- 7. TABLE ADMIN_LOGS (Audit administrateur)
-- ============================================================

CREATE TYPE admin_action_type AS ENUM (
    'user_suspended',
    'user_banned',
    'user_verified',
    'offre_moderated',
    'content_deleted',
    'settings_changed',
    'support_ticket_resolved',
    'rgpd_request_processed'
);

CREATE TABLE public.admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Administrateur
    admin_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    admin_email TEXT NOT NULL,
    
    -- Action
    action admin_action_type NOT NULL,
    description TEXT NOT NULL,
    
    -- Cible de l'action
    target_type TEXT, -- 'user', 'offre', 'entreprise', etc.
    target_id UUID,
    
    -- Détails JSON
    details JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_admin_logs_admin ON public.admin_logs(admin_id);
CREATE INDEX idx_admin_logs_action ON public.admin_logs(action);
CREATE INDEX idx_admin_logs_created ON public.admin_logs(created_at DESC);
CREATE INDEX idx_admin_logs_target ON public.admin_logs(target_type, target_id);

-- ============================================================
-- 8. TABLE RGPD_CONSENTS (Consentements RGPD)
-- ============================================================

CREATE TYPE consent_type AS ENUM (
    'cookies_essential',
    'cookies_analytics',
    'cookies_marketing',
    'data_processing',
    'marketing_emails',
    'marketing_sms'
);

CREATE TABLE public.rgpd_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Utilisateur
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Type de consentement
    consent_type consent_type NOT NULL,
    
    -- Consentement
    consented BOOLEAN NOT NULL,
    
    -- IP & User Agent
    ip_address TEXT,
    user_agent TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, consent_type)
);

-- Index
CREATE INDEX idx_rgpd_consents_user ON public.rgpd_consents(user_id);
CREATE INDEX idx_rgpd_consents_type ON public.rgpd_consents(consent_type);

-- ============================================================
-- 9. TABLE RGPD_REQUESTS (Demandes RGPD)
-- ============================================================

CREATE TYPE rgpd_request_type AS ENUM (
    'access',        -- Droit d'accès
    'rectification', -- Droit de rectification
    'deletion',      -- Droit à l'oubli
    'portability',   -- Droit à la portabilité
    'opposition'     -- Droit d'opposition
);

CREATE TYPE rgpd_request_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'rejected'
);

CREATE TABLE public.rgpd_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Utilisateur
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    user_email TEXT NOT NULL,
    
    -- Demande
    request_type rgpd_request_type NOT NULL,
    status rgpd_request_status DEFAULT 'pending',
    
    -- Description
    description TEXT,
    
    -- Traitement
    processed_by UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    response TEXT,
    
    -- Fichier export (si demande d'accès)
    export_file_url TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_rgpd_requests_user ON public.rgpd_requests(user_id);
CREATE INDEX idx_rgpd_requests_status ON public.rgpd_requests(status);
CREATE INDEX idx_rgpd_requests_type ON public.rgpd_requests(request_type);
CREATE INDEX idx_rgpd_requests_created ON public.rgpd_requests(created_at DESC);

-- ============================================================
-- 10. TABLE FAQ_QUESTIONS
-- ============================================================

CREATE TYPE faq_category AS ENUM (
    'compte',
    'candidat',
    'recruteur',
    'matching',
    'messagerie',
    'paiement',
    'rgpd',
    'technique'
);

CREATE TABLE public.faq_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Catégorie
    category faq_category NOT NULL,
    
    -- Question & Réponse
    question TEXT NOT NULL,
    reponse TEXT NOT NULL,
    
    -- SEO
    slug TEXT UNIQUE,
    
    -- Statistiques
    vues INTEGER DEFAULT 0,
    utile_count INTEGER DEFAULT 0,
    
    -- Publication
    published BOOLEAN DEFAULT true,
    ordre INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_faq_category ON public.faq_questions(category);
CREATE INDEX idx_faq_published ON public.faq_questions(published);
CREATE INDEX idx_faq_ordre ON public.faq_questions(ordre);

-- ============================================================
-- 11. TABLE SUPPORT_TICKETS
-- ============================================================

CREATE TYPE ticket_category AS ENUM (
    'technique',
    'compte',
    'paiement',
    'abus',
    'rgpd',
    'autre'
);

CREATE TYPE ticket_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);

CREATE TYPE ticket_status AS ENUM (
    'open',
    'in_progress',
    'waiting_user',
    'resolved',
    'closed'
);

CREATE TABLE public.support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Utilisateur
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    user_email TEXT NOT NULL,
    user_name TEXT,
    
    -- Ticket
    sujet TEXT NOT NULL,
    message TEXT NOT NULL,
    category ticket_category NOT NULL,
    priority ticket_priority DEFAULT 'medium',
    status ticket_status DEFAULT 'open',
    
    -- Assignation
    assigned_to UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Résolution
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    
    -- Pièces jointes
    attachments JSONB DEFAULT '[]',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_support_user ON public.support_tickets(user_id);
CREATE INDEX idx_support_status ON public.support_tickets(status);
CREATE INDEX idx_support_priority ON public.support_tickets(priority);
CREATE INDEX idx_support_assigned ON public.support_tickets(assigned_to);
CREATE INDEX idx_support_created ON public.support_tickets(created_at DESC);

-- ============================================================
-- 12. TABLE SUPPORT_TICKET_MESSAGES (Conversations support)
-- ============================================================

CREATE TABLE public.support_ticket_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES public.support_tickets(id) ON DELETE CASCADE,
    
    -- Expéditeur
    sender_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    sender_email TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    
    -- Message
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_support_messages_ticket ON public.support_ticket_messages(ticket_id);
CREATE INDEX idx_support_messages_created ON public.support_ticket_messages(created_at);

-- ============================================================
-- 13. ROW LEVEL SECURITY (RLS) - Nouvelles tables
-- ============================================================

-- Activer RLS
ALTER TABLE public.entreprises ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.swipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rgpd_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rgpd_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faq_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.support_ticket_messages ENABLE ROW LEVEL SECURITY;

-- Politiques ENTREPRISES
CREATE POLICY "Les entreprises vérifiées sont publiques"
    ON public.entreprises FOR SELECT
    USING (verified = true);

CREATE POLICY "Les recruteurs peuvent voir leur entreprise"
    ON public.entreprises FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.entreprise_id = entreprises.id
            AND recruteurs.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent modifier leur entreprise"
    ON public.entreprises FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.entreprise_id = entreprises.id
            AND recruteurs.user_id = auth.uid()
        )
    );

-- Politiques SWIPES
CREATE POLICY "Les users peuvent voir leurs propres swipes"
    ON public.swipes FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Les users peuvent créer des swipes"
    ON public.swipes FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Politiques CONVERSATIONS
CREATE POLICY "Les participants peuvent voir leurs conversations"
    ON public.conversations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.candidats
            WHERE candidats.id = conversations.candidat_id
            AND candidats.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.id = conversations.recruteur_id
            AND recruteurs.user_id = auth.uid()
        )
    );

-- Politiques MESSAGES
CREATE POLICY "Les participants peuvent voir les messages de leurs conversations"
    ON public.messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations c
            LEFT JOIN public.candidats ca ON ca.id = c.candidat_id
            LEFT JOIN public.recruteurs re ON re.id = c.recruteur_id
            WHERE c.id = messages.conversation_id
            AND (ca.user_id = auth.uid() OR re.user_id = auth.uid())
        )
    );

CREATE POLICY "Les participants peuvent envoyer des messages"
    ON public.messages FOR INSERT
    WITH CHECK (sender_id = auth.uid());

-- Politiques NOTIFICATIONS
CREATE POLICY "Les users peuvent voir leurs notifications"
    ON public.notifications FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Les users peuvent marquer leurs notifications comme lues"
    ON public.notifications FOR UPDATE
    USING (user_id = auth.uid());

-- Politiques RGPD_CONSENTS
CREATE POLICY "Les users peuvent voir leurs consentements"
    ON public.rgpd_consents FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Les users peuvent gérer leurs consentements"
    ON public.rgpd_consents FOR ALL
    USING (user_id = auth.uid());

-- Politiques RGPD_REQUESTS
CREATE POLICY "Les users peuvent voir leurs demandes RGPD"
    ON public.rgpd_requests FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Les users peuvent créer des demandes RGPD"
    ON public.rgpd_requests FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Politiques FAQ
CREATE POLICY "Tout le monde peut voir la FAQ publiée"
    ON public.faq_questions FOR SELECT
    USING (published = true);

-- Politiques SUPPORT_TICKETS
CREATE POLICY "Les users peuvent voir leurs tickets"
    ON public.support_tickets FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Les users peuvent créer des tickets"
    ON public.support_tickets FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Les users peuvent voir les messages de leurs tickets"
    ON public.support_ticket_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.support_tickets
            WHERE support_tickets.id = support_ticket_messages.ticket_id
            AND support_tickets.user_id = auth.uid()
        )
    );

-- Politiques ADMIN_LOGS (visible uniquement par les admins)
-- À compléter selon votre système de rôles admin

-- ============================================================
-- 14. TRIGGERS POUR UPDATED_AT
-- ============================================================

CREATE TRIGGER update_entreprises_updated_at BEFORE UPDATE ON public.entreprises
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON public.messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rgpd_requests_updated_at BEFORE UPDATE ON public.rgpd_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faq_updated_at BEFORE UPDATE ON public.faq_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON public.support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 15. FONCTION : CRÉER MATCH AUTOMATIQUE
-- ============================================================

CREATE OR REPLACE FUNCTION public.check_and_create_match()
RETURNS TRIGGER AS $$
DECLARE
    reciprocal_swipe_id UUID;
    conversation_id UUID;
BEGIN
    -- Si c'est un like
    IF NEW.action = 'like' OR NEW.action = 'super_like' THEN
        
        -- Chercher si l'autre a aussi liké
        IF NEW.type_swipe = 'candidat_to_offre' THEN
            -- Le candidat a liké l'offre, chercher si le recruteur a liké ce candidat
            SELECT id INTO reciprocal_swipe_id
            FROM public.swipes
            WHERE type_swipe = 'recruteur_to_candidat'
            AND candidat_id = NEW.candidat_id
            AND offre_id = NEW.offre_id
            AND (action = 'like' OR action = 'super_like')
            LIMIT 1;
            
        ELSIF NEW.type_swipe = 'recruteur_to_candidat' THEN
            -- Le recruteur a liké le candidat, chercher si le candidat a liké l'offre
            SELECT id INTO reciprocal_swipe_id
            FROM public.swipes
            WHERE type_swipe = 'candidat_to_offre'
            AND candidat_id = NEW.candidat_id
            AND offre_id = NEW.offre_id
            AND (action = 'like' OR action = 'super_like')
            LIMIT 1;
        END IF;
        
        -- Si match trouvé
        IF reciprocal_swipe_id IS NOT NULL THEN
            -- Marquer les 2 swipes comme match
            NEW.is_match = true;
            NEW.matched_at = NOW();
            
            UPDATE public.swipes
            SET is_match = true, matched_at = NOW()
            WHERE id = reciprocal_swipe_id;
            
            -- Créer une conversation
            INSERT INTO public.conversations (candidat_id, recruteur_id, offre_id, match_id)
            SELECT 
                NEW.candidat_id,
                (SELECT recruteur_id FROM public.offres WHERE id = NEW.offre_id),
                NEW.offre_id,
                NEW.id
            ON CONFLICT (candidat_id, recruteur_id, offre_id) DO NOTHING
            RETURNING id INTO conversation_id;
            
            -- Créer notifications pour les 2 parties
            INSERT INTO public.notifications (user_id, type, titre, message, data)
            SELECT 
                c.user_id,
                'new_match',
                '🎉 Nouveau Match !',
                'Vous avez un nouveau match !',
                jsonb_build_object('offre_id', NEW.offre_id, 'conversation_id', conversation_id)
            FROM public.candidats c
            WHERE c.id = NEW.candidat_id;
            
            INSERT INTO public.notifications (user_id, type, titre, message, data)
            SELECT 
                r.user_id,
                'new_match',
                '🎉 Nouveau Match !',
                'Vous avez un nouveau match !',
                jsonb_build_object('candidat_id', NEW.candidat_id, 'conversation_id', conversation_id)
            FROM public.recruteurs r
            JOIN public.offres o ON o.recruteur_id = r.id
            WHERE o.id = NEW.offre_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger pour auto-match
CREATE TRIGGER on_swipe_check_match
    BEFORE INSERT ON public.swipes
    FOR EACH ROW EXECUTE FUNCTION public.check_and_create_match();

-- ============================================================
-- 16. FONCTION : METTRE À JOUR LAST_MESSAGE CONVERSATION
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.conversations
    SET 
        last_message_at = NEW.created_at,
        last_message_preview = LEFT(NEW.contenu, 100)
    WHERE id = NEW.conversation_id;
    
    -- Créer notification pour le destinataire
    INSERT INTO public.notifications (user_id, type, titre, message, link_url, data)
    SELECT 
        CASE 
            WHEN c.user_id = NEW.sender_id THEN r.user_id
            ELSE c.user_id
        END,
        'new_message',
        'Nouveau message',
        LEFT(NEW.contenu, 50),
        '/messages/' || NEW.conversation_id,
        jsonb_build_object('conversation_id', NEW.conversation_id, 'message_id', NEW.id)
    FROM public.conversations conv
    LEFT JOIN public.candidats c ON c.id = conv.candidat_id
    LEFT JOIN public.recruteurs r ON r.id = conv.recruteur_id
    WHERE conv.id = NEW.conversation_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger
CREATE TRIGGER on_message_update_conversation
    AFTER INSERT ON public.messages
    FOR EACH ROW EXECUTE FUNCTION public.update_conversation_last_message();

-- ============================================================
-- FIN DES NOUVELLES TABLES V2
-- ============================================================

-- ✅ RÉSUMÉ DES NOUVELLES TABLES :
-- - entreprises (infos détaillées des sociétés)
-- - swipes (système like/dislike type Tinder)
-- - conversations (messagerie entre matchs)
-- - messages (messages dans conversations)
-- - notifications (système de notifications)
-- - admin_logs (audit administrateur)
-- - rgpd_consents (consentements RGPD)
-- - rgpd_requests (demandes RGPD)
-- - faq_questions (base de connaissances)
-- - support_tickets (tickets support)
-- - support_ticket_messages (messages support)
