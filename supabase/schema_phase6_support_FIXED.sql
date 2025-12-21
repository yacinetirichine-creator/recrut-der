-- ================================================
-- 📊 PHASE 6: AGENT IA & SUPPORT - VERSION SIMPLIFIÉE
-- Test étape par étape
-- ================================================

-- ÉTAPE 1: Table chatbot_conversations
CREATE TABLE IF NOT EXISTS public.chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatbot_conversations_user ON public.chatbot_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_conversations_updated ON public.chatbot_conversations(updated_at DESC);

-- ÉTAPE 2: FAQ - La table existe déjà, pas besoin de la recréer
-- Juste s'assurer que les index existent

CREATE INDEX IF NOT EXISTS idx_faq_vues ON public.faq_questions(vues DESC);

-- ÉTAPE 3: Table support_ticket_messages
CREATE TABLE IF NOT EXISTS public.support_ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES public.support_tickets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    is_staff BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON public.support_ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_created ON public.support_ticket_messages(created_at);

-- ÉTAPE 4: Ajouter closed_at à support_tickets
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'support_tickets' AND column_name = 'closed_at'
    ) THEN
        ALTER TABLE public.support_tickets ADD COLUMN closed_at TIMESTAMPTZ;
    END IF;
END $$;

-- ÉTAPE 5: RLS sur chatbot_conversations
ALTER TABLE public.chatbot_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS chatbot_conversations_user_policy ON public.chatbot_conversations;
CREATE POLICY chatbot_conversations_user_policy ON public.chatbot_conversations
    FOR ALL
    USING (user_id = auth.uid());

-- ÉTAPE 6: RLS sur FAQ
ALTER TABLE public.faq_questions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS faq_read_policy ON public.faq_questions;
CREATE POLICY faq_read_policy ON public.faq_questions
    FOR SELECT
    USING (published = true);

-- ÉTAPE 7: RLS sur support_ticket_messages
ALTER TABLE public.support_ticket_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ticket_messages_user_policy ON public.support_ticket_messages;
CREATE POLICY ticket_messages_user_policy ON public.support_ticket_messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.support_tickets 
            WHERE public.support_tickets.id = public.support_ticket_messages.ticket_id 
            AND public.support_tickets.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS ticket_messages_insert_policy ON public.support_ticket_messages;
CREATE POLICY ticket_messages_insert_policy ON public.support_ticket_messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.support_tickets 
            WHERE public.support_tickets.id = public.support_ticket_messages.ticket_id 
            AND public.support_tickets.user_id = auth.uid()
        )
    );

-- ÉTAPE 8: Données FAQ
INSERT INTO public.faq_questions (question, reponse, category, published) VALUES
('Comment créer mon profil candidat ?', 'Pour créer votre profil, inscrivez-vous en tant que candidat, remplissez vos informations personnelles et téléchargez votre CV. Notre IA analysera automatiquement vos compétences.', 'compte', true),
('Comment fonctionne le matching ?', 'Le matching fonctionne comme Tinder : swipez à droite sur les offres qui vous intéressent. Si le recruteur vous like aussi, c''est un match ! Vous pouvez ensuite échanger via la messagerie.', 'matching', true),
('Puis-je modifier mon CV après l''avoir uploadé ?', 'Oui, rendez-vous dans votre profil et téléchargez un nouveau CV. L''IA réanalysera automatiquement vos compétences.', 'compte', true),
('Comment publier une offre d''emploi ?', 'En tant que recruteur, créez d''abord votre entreprise, puis cliquez sur "Nouvelle offre". Remplissez les détails du poste et publiez. L''offre sera visible par les candidats correspondants.', 'recruteur', true),
('Combien coûte la plateforme ?', 'Recrut''der propose une formule gratuite pour les candidats et une version premium pour les recruteurs avec fonctionnalités avancées.', 'paiement', true),
('Mes données sont-elles sécurisées ?', 'Oui, nous respectons le RGPD. Vos données sont chiffrées et vous pouvez exercer vos droits (accès, rectification, suppression) à tout moment.', 'rgpd', true),
('Comment annuler un match ?', 'Vous ne pouvez pas annuler un match directement, mais vous pouvez bloquer un utilisateur ou signaler un profil inapproprié.', 'matching', true),
('Pourquoi je ne vois plus de profils/offres ?', 'Si vous avez swipé tous les profils disponibles correspondant à vos critères, revenez plus tard ou élargissez vos filtres de recherche.', 'matching', true),
('Comment contacter le support ?', 'Utilisez le chatbot en bas à droite ou créez un ticket de support depuis votre espace personnel. Notre équipe répond sous 24-48h.', 'technique', true),
('Puis-je supprimer mon compte ?', 'Oui, rendez-vous dans Paramètres > Confidentialité > Supprimer mon compte. Cette action est irréversible.', 'compte', true)
ON CONFLICT DO NOTHING;

-- ÉTAPE 9: Fonctions
CREATE OR REPLACE FUNCTION cleanup_old_chatbot_conversations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.chatbot_conversations
    WHERE updated_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_chatbot_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_chatbot_conversation ON public.chatbot_conversations;
CREATE TRIGGER trigger_update_chatbot_conversation
    BEFORE UPDATE ON public.chatbot_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_chatbot_conversation_timestamp();

-- ÉTAPE 10: Vue stats
CREATE OR REPLACE VIEW public.faq_stats AS
SELECT 
    category,
    COUNT(*) as total_questions,
    SUM(vues) as total_views,
    AVG(vues)::INTEGER as avg_views,
    COUNT(*) FILTER (WHERE published = true) as published_count
FROM public.faq_questions
GROUP BY category;
