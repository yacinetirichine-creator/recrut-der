-- ================================================
-- 📊 PHASE 8: INTÉGRATIONS JOB BOARDS
-- LinkedIn, Indeed, Pôle Emploi, WTTJ
-- ================================================

-- Table: Offres importées depuis job boards externes
CREATE TABLE IF NOT EXISTS public.external_job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source
    source VARCHAR(50) NOT NULL,  -- indeed, linkedin, pole_emploi, wttj
    external_id VARCHAR(255) NOT NULL,  -- ID de l'offre sur la plateforme externe
    
    -- Informations de l'offre
    titre TEXT NOT NULL,
    entreprise_nom TEXT NOT NULL,
    description TEXT,
    localisation TEXT,
    type_contrat VARCHAR(50),  -- CDI, CDD, Stage, Alternance, Freelance
    salaire_min INTEGER,
    salaire_max INTEGER,
    salaire_devise VARCHAR(10) DEFAULT 'EUR',
    
    -- Compétences et exigences
    competences_requises TEXT[],
    experience_requise VARCHAR(50),
    niveau_etude VARCHAR(50),
    
    -- URLs
    url_offre TEXT,
    url_candidature TEXT,
    logo_url TEXT,
    
    -- Synchronisation
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Mapping vers notre système
    offre_id UUID REFERENCES public.offres(id) ON DELETE SET NULL,  -- Si converti en offre locale
    
    -- Metadata brute
    raw_data JSONB DEFAULT '{}'::jsonb,
    
    UNIQUE(source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_external_jobs_source ON public.external_job_postings(source);
CREATE INDEX IF NOT EXISTS idx_external_jobs_active ON public.external_job_postings(is_active);
CREATE INDEX IF NOT EXISTS idx_external_jobs_imported ON public.external_job_postings(imported_at DESC);
CREATE INDEX IF NOT EXISTS idx_external_jobs_offre ON public.external_job_postings(offre_id);

-- Table: Logs de synchronisation
CREATE TABLE IF NOT EXISTS public.job_board_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running',  -- running, success, failed, partial
    
    -- Statistiques
    total_fetched INTEGER DEFAULT 0,
    total_imported INTEGER DEFAULT 0,
    total_updated INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    
    -- Détails
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_source ON public.job_board_sync_logs(source);
CREATE INDEX IF NOT EXISTS idx_sync_logs_started ON public.job_board_sync_logs(started_at DESC);

-- Table: Configuration des sources externes
CREATE TABLE IF NOT EXISTS public.job_board_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) UNIQUE NOT NULL,
    
    -- Configuration
    enabled BOOLEAN DEFAULT true,
    api_endpoint TEXT,
    sync_frequency_hours INTEGER DEFAULT 24,
    last_sync_at TIMESTAMPTZ,
    
    -- Filtres par défaut
    default_filters JSONB DEFAULT '{}'::jsonb,  -- {"location": "France", "type": ["CDI", "CDD"]}
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insérer configurations par défaut
INSERT INTO public.job_board_configs (source, api_endpoint, sync_frequency_hours, default_filters) VALUES
('indeed', 'https://api.indeed.com/ads/apisearch', 24, '{"location": "France", "limit": 100}'::jsonb),
('linkedin', 'https://api.linkedin.com/v2/jobPostings', 24, '{"country": "FR", "limit": 50}'::jsonb)
ON CONFLICT (source) DO NOTHING;

-- Table: Mapping des compétences externes vers nos compétences
CREATE TABLE IF NOT EXISTS public.skill_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_skill TEXT NOT NULL,
    internal_skill TEXT NOT NULL,
    source VARCHAR(50),  -- Si spécifique à une plateforme
    confidence DECIMAL(3,2) DEFAULT 1.0,  -- Score de confiance du mapping
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(external_skill, source)
);

CREATE INDEX IF NOT EXISTS idx_skill_mappings_external ON public.skill_mappings(external_skill);
CREATE INDEX IF NOT EXISTS idx_skill_mappings_internal ON public.skill_mappings(internal_skill);

-- ================================================
-- RLS POLICIES
-- ================================================

-- external_job_postings: Lecture publique, écriture admin uniquement
ALTER TABLE public.external_job_postings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS external_jobs_read_policy ON public.external_job_postings;
CREATE POLICY external_jobs_read_policy ON public.external_job_postings
    FOR SELECT
    USING (is_active = true);

DROP POLICY IF EXISTS external_jobs_admin_policy ON public.external_job_postings;
CREATE POLICY external_jobs_admin_policy ON public.external_job_postings
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- job_board_sync_logs: Admin uniquement
ALTER TABLE public.job_board_sync_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sync_logs_admin_policy ON public.job_board_sync_logs;
CREATE POLICY sync_logs_admin_policy ON public.job_board_sync_logs
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- job_board_configs: Admin uniquement
ALTER TABLE public.job_board_configs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS configs_admin_policy ON public.job_board_configs;
CREATE POLICY configs_admin_policy ON public.job_board_configs
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- skill_mappings: Lecture publique, écriture admin
ALTER TABLE public.skill_mappings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS skill_mappings_read_policy ON public.skill_mappings;
CREATE POLICY skill_mappings_read_policy ON public.skill_mappings
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS skill_mappings_insert_policy ON public.skill_mappings;
CREATE POLICY skill_mappings_insert_policy ON public.skill_mappings
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

DROP POLICY IF EXISTS skill_mappings_update_policy ON public.skill_mappings;
CREATE POLICY skill_mappings_update_policy ON public.skill_mappings
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

DROP POLICY IF EXISTS skill_mappings_delete_policy ON public.skill_mappings;
CREATE POLICY skill_mappings_delete_policy ON public.skill_mappings
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.utilisateurs 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ================================================
-- FONCTIONS UTILITAIRES
-- ================================================

-- Fonction pour mettre à jour last_synced_at
CREATE OR REPLACE FUNCTION update_external_job_sync_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_synced_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_external_job_sync ON public.external_job_postings;
CREATE TRIGGER trigger_update_external_job_sync
    BEFORE UPDATE ON public.external_job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_external_job_sync_timestamp();

-- Fonction pour nettoyer les offres inactives anciennes
CREATE OR REPLACE FUNCTION cleanup_old_external_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.external_job_postings
    WHERE is_active = false 
      AND last_synced_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour mapper compétences externes vers internes
CREATE OR REPLACE FUNCTION map_external_skill(p_skill TEXT, p_source VARCHAR DEFAULT NULL)
RETURNS TEXT AS $$
DECLARE
    mapped_skill TEXT;
BEGIN
    SELECT internal_skill INTO mapped_skill
    FROM public.skill_mappings
    WHERE external_skill = p_skill
      AND (source = p_source OR source IS NULL)
    ORDER BY confidence DESC
    LIMIT 1;
    
    RETURN COALESCE(mapped_skill, p_skill);
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- VUES UTILES
-- ================================================

-- Vue: Stats des imports par source
CREATE OR REPLACE VIEW public.job_board_import_stats AS
SELECT 
    source,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE is_active = true) as active_jobs,
    COUNT(*) FILTER (WHERE offre_id IS NOT NULL) as converted_to_local,
    MAX(imported_at) as last_import,
    AVG(EXTRACT(EPOCH FROM (last_synced_at - imported_at))) as avg_age_seconds
FROM public.external_job_postings
GROUP BY source;

-- Vue: Dernières synchronisations
CREATE OR REPLACE VIEW public.recent_sync_activity AS
SELECT 
    s.*,
    c.enabled as source_enabled,
    c.sync_frequency_hours
FROM public.job_board_sync_logs s
LEFT JOIN public.job_board_configs c ON s.source = c.source
ORDER BY s.started_at DESC
LIMIT 50;

-- Vue: Offres externes actives avec mapping
CREATE OR REPLACE VIEW public.active_external_jobs AS
SELECT 
    ejp.*,
    o.id as local_offre_id,
    o.titre as local_titre,
    CASE 
        WHEN ejp.offre_id IS NOT NULL THEN 'converted'
        WHEN ejp.is_active THEN 'active'
        ELSE 'inactive'
    END as status
FROM public.external_job_postings ejp
LEFT JOIN public.offres o ON ejp.offre_id = o.id
WHERE ejp.is_active = true
ORDER BY ejp.imported_at DESC;
