-- ================================================
-- 📊 PHASE 6: AGENT IA & SUPPORT
-- Chatbot, FAQ dynamique, tickets support
-- ================================================

-- Table: Conversations chatbot
CREATE TABLE IF NOT EXISTS chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatbot_conversations_user ON chatbot_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_conversations_updated ON chatbot_conversations(updated_at DESC);

-- Table: FAQ Questions
CREATE TABLE IF NOT EXISTS faq_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    published BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ajouter la colonne views si elle n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'faq_questions' AND column_name = 'views'
    ) THEN
        ALTER TABLE public.faq_questions ADD COLUMN views INTEGER DEFAULT 0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_faq_published ON faq_questions(published);
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_questions(category);
CREATE INDEX IF NOT EXISTS idx_faq_views ON faq_questions(views DESC);

-- Table: Messages des tickets support
CREATE TABLE IF NOT EXISTS support_ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.support_tickets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    is_staff BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON support_ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_created ON support_ticket_messages(created_at);

-- Ajouter colonnes manquantes à support_tickets si nécessaire
DO $$ 
BEGIN
    -- Vérifier si la colonne closed_at existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'support_tickets' AND column_name = 'closed_at'
    ) THEN
        ALTER TABLE public.support_tickets ADD COLUMN closed_at TIMESTAMPTZ;
    END IF;
END $$;

-- ================================================
-- RLS POLICIES
-- ================================================

-- Chatbot conversations: utilisateur peut voir/modifier ses propres conversations
ALTER TABLE chatbot_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS chatbot_conversations_user_policy ON chatbot_conversations;
CREATE POLICY chatbot_conversations_user_policy ON chatbot_conversations
    FOR ALL
    USING (user_id = auth.uid());

-- FAQ: tout le monde peut lire les FAQ publiées
ALTER TABLE faq_questions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS faq_read_policy ON faq_questions;
CREATE POLICY faq_read_policy ON faq_questions
    FOR SELECT
    USING (published = true);

-- Support ticket messages: utilisateur peut voir ses messages
ALTER TABLE support_ticket_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ticket_messages_user_policy ON support_ticket_messages;
CREATE POLICY ticket_messages_user_policy ON support_ticket_messages
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR 
        EXISTS (
            SELECT 1 FROM public.support_tickets 
            WHERE public.support_tickets.id = ticket_id 
            AND public.support_tickets.user_id = auth.uid()
        )
    );

-- Permettre aux utilisateurs d'ajouter des messages à leurs tickets
DROP POLICY IF EXISTS ticket_messages_insert_policy ON support_ticket_messages;
CREATE POLICY ticket_messages_insert_policy ON support_ticket_messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.support_tickets 
            WHERE public.support_tickets.id = ticket_id 
            AND public.support_tickets.user_id = auth.uid()
        )
    );

-- ================================================
-- DONNÉES INITIALES FAQ
-- ================================================

INSERT INTO faq_questions (question, answer, category, published) VALUES
('Comment créer mon profil candidat ?', 'Pour créer votre profil, inscrivez-vous en tant que candidat, remplissez vos informations personnelles et téléchargez votre CV. Notre IA analysera automatiquement vos compétences.', 'Compte & Profil', true),
('Comment fonctionne le matching ?', 'Le matching fonctionne comme Tinder : swipez à droite sur les offres qui vous intéressent. Si le recruteur vous like aussi, c''est un match ! Vous pouvez ensuite échanger via la messagerie.', 'Matching', true),
('Puis-je modifier mon CV après l''avoir uploadé ?', 'Oui, rendez-vous dans votre profil et téléchargez un nouveau CV. L''IA réanalysera automatiquement vos compétences.', 'Compte & Profil', true),
('Comment publier une offre d''emploi ?', 'En tant que recruteur, créez d''abord votre entreprise, puis cliquez sur "Nouvelle offre". Remplissez les détails du poste et publiez. L''offre sera visible par les candidats correspondants.', 'Recruteurs', true),
('Combien coûte la plateforme ?', 'Recrut''der propose une formule gratuite pour les candidats et une version premium pour les recruteurs avec fonctionnalités avancées. Consultez notre page tarifs pour plus de détails.', 'Tarifs', true),
('Mes données sont-elles sécurisées ?', 'Oui, nous respectons le RGPD. Vos données sont chiffrées et vous pouvez exercer vos droits (accès, rectification, suppression) à tout moment.', 'Sécurité & RGPD', true),
('Comment annuler un match ?', 'Vous ne pouvez pas annuler un match directement, mais vous pouvez bloquer un utilisateur ou signaler un profil inapproprié.', 'Matching', true),
('Pourquoi je ne vois plus de profils/offres ?', 'Si vous avez swipé tous les profils disponibles correspondant à vos critères, revenez plus tard ou élargissez vos filtres de recherche.', 'Matching', true),
('Comment contacter le support ?', 'Utilisez le chatbot en bas à droite ou créez un ticket de support depuis votre espace personnel. Notre équipe répond sous 24-48h.', 'Support', true),
('Puis-je supprimer mon compte ?', 'Oui, rendez-vous dans Paramètres > Confidentialité > Supprimer mon compte. Cette action est irréversible.', 'Compte & Profil', true)
ON CONFLICT DO NOTHING;

-- ================================================
-- FONCTIONS UTILITAIRES
-- ================================================

-- Fonction pour nettoyer les anciennes conversations (plus de 90 jours)
CREATE OR REPLACE FUNCTION cleanup_old_chatbot_conversations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chatbot_conversations
    WHERE updated_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour updated_at sur chatbot_conversations
CREATE OR REPLACE FUNCTION update_chatbot_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_chatbot_conversation ON chatbot_conversations;
CREATE TRIGGER trigger_update_chatbot_conversation
    BEFORE UPDATE ON chatbot_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_chatbot_conversation_timestamp();

-- Vue: Stats FAQ
CREATE OR REPLACE VIEW faq_stats AS
SELECT 
    category,
    COUNT(*) as total_questions,
    SUM(views) as total_views,
    AVG(views)::INTEGER as avg_views,
    COUNT(*) FILTER (WHERE published = true) as published_count
FROM faq_questions
GROUP BY category;
