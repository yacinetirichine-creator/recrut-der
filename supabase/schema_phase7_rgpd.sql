-- ================================================
-- 📊 PHASE 7: RGPD & PROTECTION DONNÉES
-- Suppression compte, audit, consentements
-- ================================================

-- Table: Logs de suppression de comptes (audit RGPD)
CREATE TABLE IF NOT EXISTS public.account_deletions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,  -- Pas de FK car user sera supprimé
    user_email TEXT,
    user_type TEXT,
    reason TEXT,
    deleted_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_account_deletions_date ON public.account_deletions(deleted_at DESC);
CREATE INDEX IF NOT EXISTS idx_account_deletions_email ON public.account_deletions(user_email);

-- Table: Consentements RGPD
CREATE TABLE IF NOT EXISTS public.user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,  -- cookies, marketing, analytics, etc.
    consented BOOLEAN NOT NULL DEFAULT false,
    consented_at TIMESTAMPTZ,
    withdrawn_at TIMESTAMPTZ,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_consents_user ON public.user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON public.user_consents(consent_type);

-- Table: Logs d'accès aux données (audit)
CREATE TABLE IF NOT EXISTS public.data_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,  -- export, view, modify, delete
    data_type VARCHAR(50),  -- profil, cv, messages, etc.
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_access_logs_user ON public.data_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_action ON public.data_access_logs(action);
CREATE INDEX IF NOT EXISTS idx_data_access_logs_date ON public.data_access_logs(created_at DESC);

-- ================================================
-- RLS POLICIES
-- ================================================

-- account_deletions: Accessible uniquement par les admins
ALTER TABLE public.account_deletions ENABLE ROW LEVEL SECURITY;

-- Pas de policy pour les users normaux (admin only via service role)

-- user_consents: Utilisateur peut voir/modifier ses propres consentements
ALTER TABLE public.user_consents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_consents_user_policy ON public.user_consents;
CREATE POLICY user_consents_user_policy ON public.user_consents
    FOR ALL
    USING (user_id = auth.uid());

-- data_access_logs: Utilisateur peut voir ses propres logs
ALTER TABLE public.data_access_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS data_access_logs_user_policy ON public.data_access_logs;
CREATE POLICY data_access_logs_user_policy ON public.data_access_logs
    FOR SELECT
    USING (user_id = auth.uid());

-- ================================================
-- FONCTIONS UTILITAIRES
-- ================================================

-- Fonction pour anonymiser un utilisateur (soft delete)
CREATE OR REPLACE FUNCTION anonymize_user(target_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Anonymiser l'utilisateur
    UPDATE public.utilisateurs
    SET 
        email = 'deleted_' || target_user_id || '@recrut-der.com',
        nom = 'Utilisateur',
        prenom = 'Supprimé',
        telephone = NULL,
        photo_url = NULL,
        bio = NULL,
        linkedin_url = NULL
    WHERE id = target_user_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer la taille des données d'un utilisateur
CREATE OR REPLACE FUNCTION get_user_data_size(target_user_id UUID)
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'candidats'::TEXT, COUNT(*)::BIGINT FROM public.candidats WHERE user_id = target_user_id
    UNION ALL
    SELECT 'recruteurs'::TEXT, COUNT(*)::BIGINT FROM public.recruteurs WHERE user_id = target_user_id
    UNION ALL
    SELECT 'matchings'::TEXT, COUNT(*)::BIGINT FROM public.matchings WHERE candidat_id = target_user_id OR recruteur_id = target_user_id
    UNION ALL
    SELECT 'messages'::TEXT, COUNT(*)::BIGINT FROM public.messages WHERE expediteur_id = target_user_id OR destinataire_id = target_user_id
    UNION ALL
    SELECT 'swipes'::TEXT, COUNT(*)::BIGINT FROM public.swipes WHERE candidat_id = target_user_id OR recruteur_id = target_user_id
    UNION ALL
    SELECT 'notifications'::TEXT, COUNT(*)::BIGINT FROM public.notifications WHERE utilisateur_id = target_user_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour logger les accès aux données sensibles
CREATE OR REPLACE FUNCTION log_data_access()
RETURNS TRIGGER AS $$
BEGIN
    -- Logger l'accès (à implémenter selon les besoins)
    -- Pour l'instant, juste un placeholder
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- VUES UTILES
-- ================================================

-- Vue: Statistiques de suppression de comptes
CREATE OR REPLACE VIEW public.account_deletion_stats AS
SELECT 
    DATE(deleted_at) as deletion_date,
    user_type,
    COUNT(*) as total_deletions,
    COUNT(CASE WHEN reason IS NOT NULL THEN 1 END) as deletions_with_reason
FROM public.account_deletions
GROUP BY DATE(deleted_at), user_type
ORDER BY deletion_date DESC;

-- Vue: Consentements par type
CREATE OR REPLACE VIEW public.consent_stats AS
SELECT 
    consent_type,
    COUNT(*) as total_users,
    COUNT(CASE WHEN consented = true THEN 1 END) as consented_count,
    COUNT(CASE WHEN consented = false THEN 1 END) as not_consented_count,
    ROUND(100.0 * COUNT(CASE WHEN consented = true THEN 1 END) / COUNT(*), 2) as consent_rate
FROM public.user_consents
GROUP BY consent_type;

-- ================================================
-- DONNÉES INITIALES
-- ================================================

-- Types de consentements par défaut
-- Les consentements seront créés dynamiquement lors de l'inscription
-- Pas d'INSERT ici car dépend des utilisateurs
