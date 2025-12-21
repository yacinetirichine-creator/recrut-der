-- ╔═══════════════════════════════════════════════════════════════╗
-- ║  RECRUT'DER - Schéma Base de Données Supabase                ║
-- ║  Plateforme de matching IA candidats/recruteurs              ║
-- ╚═══════════════════════════════════════════════════════════════╝

-- ============================================================
-- 1. EXTENSION POUR UUID
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 2. TYPES ENUM
-- ============================================================

CREATE TYPE type_utilisateur AS ENUM ('candidat', 'recruteur');
CREATE TYPE type_contrat AS ENUM ('cdi', 'cdd', 'freelance', 'stage', 'alternance');
CREATE TYPE teletravail AS ENUM ('full_remote', 'hybride', 'presentiel');
CREATE TYPE disponibilite AS ENUM ('immediate', '1_mois', '3_mois', 'flexible');

-- ============================================================
-- 3. TABLE UTILISATEURS (étend auth.users de Supabase)
-- ============================================================

CREATE TABLE public.utilisateurs (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    type_utilisateur type_utilisateur NOT NULL,
    email TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT,
    telephone TEXT,
    photo_url TEXT,
    bio TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche rapide
CREATE INDEX idx_utilisateurs_type ON public.utilisateurs(type_utilisateur);
CREATE INDEX idx_utilisateurs_email ON public.utilisateurs(email);

-- ============================================================
-- 4. TABLE CANDIDATS
-- ============================================================

CREATE TABLE public.candidats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Compétences
    competences_techniques TEXT[] DEFAULT '{}',
    soft_skills TEXT[] DEFAULT '{}',
    
    -- Expérience
    experience_annees INTEGER DEFAULT 0,
    
    -- Formation
    qualifications TEXT[] DEFAULT '{}',
    niveau_etudes TEXT DEFAULT 'bac+3',
    
    -- Salaire
    salaire_min INTEGER NOT NULL,
    salaire_max INTEGER NOT NULL,
    
    -- Localisation
    localisation TEXT NOT NULL,
    accept_remote BOOLEAN DEFAULT false,
    preference_teletravail teletravail DEFAULT 'hybride',
    
    -- Préférences
    secteurs TEXT[] DEFAULT '{}',
    type_contrat_souhaite type_contrat[] DEFAULT '{cdi}',
    disponibilite disponibilite DEFAULT '1_mois',
    langues TEXT[] DEFAULT '{français}',
    taille_entreprise_preferee TEXT[] DEFAULT '{}',
    
    -- Metadata
    cv_url TEXT,
    portfolio_url TEXT,
    actif BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT salaire_valid CHECK (salaire_min <= salaire_max)
);

-- Index pour matching rapide
CREATE INDEX idx_candidats_user_id ON public.candidats(user_id);
CREATE INDEX idx_candidats_localisation ON public.candidats(localisation);
CREATE INDEX idx_candidats_competences ON public.candidats USING GIN(competences_techniques);
CREATE INDEX idx_candidats_actif ON public.candidats(actif);

-- ============================================================
-- 5. TABLE RECRUTEURS
-- ============================================================

CREATE TABLE public.recruteurs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Entreprise
    entreprise TEXT NOT NULL,
    poste TEXT,
    secteur TEXT,
    taille_entreprise TEXT,
    site_web TEXT,
    
    -- Metadata
    actif BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_recruteurs_user_id ON public.recruteurs(user_id);
CREATE INDEX idx_recruteurs_entreprise ON public.recruteurs(entreprise);

-- ============================================================
-- 6. TABLE OFFRES
-- ============================================================

CREATE TABLE public.offres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruteur_id UUID REFERENCES public.recruteurs(id) ON DELETE CASCADE,
    
    -- Informations de base
    titre TEXT NOT NULL,
    entreprise TEXT NOT NULL,
    description TEXT,
    
    -- Compétences
    competences_requises TEXT[] DEFAULT '{}',
    competences_bonus TEXT[] DEFAULT '{}',
    soft_skills_recherches TEXT[] DEFAULT '{}',
    
    -- Expérience
    experience_min INTEGER DEFAULT 0,
    experience_max INTEGER DEFAULT 50,
    
    -- Formation
    qualifications_requises TEXT[] DEFAULT '{}',
    qualifications_bonus TEXT[] DEFAULT '{}',
    niveau_etudes_min TEXT DEFAULT 'bac+3',
    
    -- Salaire
    salaire_min INTEGER NOT NULL,
    salaire_max INTEGER NOT NULL,
    
    -- Localisation
    localisation TEXT NOT NULL,
    remote_possible BOOLEAN DEFAULT false,
    politique_teletravail teletravail DEFAULT 'hybride',
    
    -- Détails contrat
    secteur TEXT,
    type_contrat type_contrat DEFAULT 'cdi',
    date_debut_souhaitee disponibilite DEFAULT '1_mois',
    
    -- Langues
    langues_requises TEXT[] DEFAULT '{français}',
    langues_bonus TEXT[] DEFAULT '{}',
    
    -- Entreprise
    taille_entreprise TEXT DEFAULT 'pme',
    
    -- Metadata
    publiee BOOLEAN DEFAULT true,
    expiration_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT offre_salaire_valid CHECK (salaire_min <= salaire_max)
);

-- Index pour recherche rapide
CREATE INDEX idx_offres_recruteur ON public.offres(recruteur_id);
CREATE INDEX idx_offres_localisation ON public.offres(localisation);
CREATE INDEX idx_offres_competences ON public.offres USING GIN(competences_requises);
CREATE INDEX idx_offres_publiee ON public.offres(publiee);
CREATE INDEX idx_offres_type_contrat ON public.offres(type_contrat);

-- ============================================================
-- 7. TABLE MATCHINGS (résultats de matching sauvegardés)
-- ============================================================

CREATE TABLE public.matchings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidat_id UUID REFERENCES public.candidats(id) ON DELETE CASCADE,
    offre_id UUID REFERENCES public.offres(id) ON DELETE CASCADE,
    
    -- Score
    score_global DECIMAL(5,2) NOT NULL,
    score_competences DECIMAL(5,2),
    score_experience DECIMAL(5,2),
    score_qualifications DECIMAL(5,2),
    score_salaire DECIMAL(5,2),
    score_localisation DECIMAL(5,2),
    
    -- Détails
    detail_json JSONB,
    
    -- Actions
    vu_par_candidat BOOLEAN DEFAULT false,
    vu_par_recruteur BOOLEAN DEFAULT false,
    interesse_candidat BOOLEAN,
    interesse_recruteur BOOLEAN,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(candidat_id, offre_id)
);

-- Index pour recherche rapide
CREATE INDEX idx_matchings_candidat ON public.matchings(candidat_id);
CREATE INDEX idx_matchings_offre ON public.matchings(offre_id);
CREATE INDEX idx_matchings_score ON public.matchings(score_global DESC);
CREATE INDEX idx_matchings_interesse ON public.matchings(interesse_candidat, interesse_recruteur);

-- ============================================================
-- 8. TABLE CANDIDATURES
-- ============================================================

CREATE TABLE public.candidatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidat_id UUID REFERENCES public.candidats(id) ON DELETE CASCADE,
    offre_id UUID REFERENCES public.offres(id) ON DELETE CASCADE,
    matching_id UUID REFERENCES public.matchings(id) ON DELETE SET NULL,
    
    -- Statut
    statut TEXT DEFAULT 'envoyee',
    message_motivation TEXT,
    
    -- Suivi
    lue_par_recruteur BOOLEAN DEFAULT false,
    reponse_recruteur TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(candidat_id, offre_id)
);

-- Index
CREATE INDEX idx_candidatures_candidat ON public.candidatures(candidat_id);
CREATE INDEX idx_candidatures_offre ON public.candidatures(offre_id);
CREATE INDEX idx_candidatures_statut ON public.candidatures(statut);

-- ============================================================
-- 9. ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Activer RLS sur toutes les tables
ALTER TABLE public.utilisateurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recruteurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.offres ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matchings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidatures ENABLE ROW LEVEL SECURITY;

-- Politiques UTILISATEURS
CREATE POLICY "Les utilisateurs peuvent voir leur propre profil"
    ON public.utilisateurs FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Les utilisateurs peuvent modifier leur propre profil"
    ON public.utilisateurs FOR UPDATE
    USING (auth.uid() = id);

-- Politiques CANDIDATS
CREATE POLICY "Les candidats peuvent voir leur profil"
    ON public.candidats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Les recruteurs peuvent voir les candidats actifs"
    ON public.candidats FOR SELECT
    USING (actif = true);

CREATE POLICY "Les candidats peuvent modifier leur profil"
    ON public.candidats FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Les candidats peuvent créer leur profil"
    ON public.candidats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Politiques RECRUTEURS
CREATE POLICY "Les recruteurs peuvent voir leur profil"
    ON public.recruteurs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Les recruteurs peuvent modifier leur profil"
    ON public.recruteurs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Les recruteurs peuvent créer leur profil"
    ON public.recruteurs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Politiques OFFRES
CREATE POLICY "Tout le monde peut voir les offres publiées"
    ON public.offres FOR SELECT
    USING (publiee = true);

CREATE POLICY "Les recruteurs peuvent voir leurs propres offres"
    ON public.offres FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.id = offres.recruteur_id
            AND recruteurs.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent créer des offres"
    ON public.offres FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.id = recruteur_id
            AND recruteurs.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent modifier leurs offres"
    ON public.offres FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.id = offres.recruteur_id
            AND recruteurs.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent supprimer leurs offres"
    ON public.offres FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.recruteurs
            WHERE recruteurs.id = offres.recruteur_id
            AND recruteurs.user_id = auth.uid()
        )
    );

-- Politiques MATCHINGS
CREATE POLICY "Les candidats peuvent voir leurs matchings"
    ON public.matchings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.candidats
            WHERE candidats.id = matchings.candidat_id
            AND candidats.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent voir les matchings de leurs offres"
    ON public.matchings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.offres
            JOIN public.recruteurs ON recruteurs.id = offres.recruteur_id
            WHERE offres.id = matchings.offre_id
            AND recruteurs.user_id = auth.uid()
        )
    );

-- Politiques CANDIDATURES
CREATE POLICY "Les candidats peuvent voir leurs candidatures"
    ON public.candidatures FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.candidats
            WHERE candidats.id = candidatures.candidat_id
            AND candidats.user_id = auth.uid()
        )
    );

CREATE POLICY "Les recruteurs peuvent voir les candidatures à leurs offres"
    ON public.candidatures FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.offres
            JOIN public.recruteurs ON recruteurs.id = offres.recruteur_id
            WHERE offres.id = candidatures.offre_id
            AND recruteurs.user_id = auth.uid()
        )
    );

CREATE POLICY "Les candidats peuvent créer des candidatures"
    ON public.candidatures FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.candidats
            WHERE candidats.id = candidat_id
            AND candidats.user_id = auth.uid()
        )
    );

-- ============================================================
-- 10. TRIGGERS POUR UPDATED_AT
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_utilisateurs_updated_at BEFORE UPDATE ON public.utilisateurs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidats_updated_at BEFORE UPDATE ON public.candidats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recruteurs_updated_at BEFORE UPDATE ON public.recruteurs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_offres_updated_at BEFORE UPDATE ON public.offres
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matchings_updated_at BEFORE UPDATE ON public.matchings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidatures_updated_at BEFORE UPDATE ON public.candidatures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 11. FONCTION POUR CRÉER UN UTILISATEUR APRÈS INSCRIPTION
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.utilisateurs (id, email, nom, type_utilisateur)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'nom', 'Nouvel utilisateur'),
        COALESCE(NEW.raw_user_meta_data->>'type_utilisateur', 'candidat')::type_utilisateur
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger pour auto-création utilisateur
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- FIN DU SCHÉMA
-- ============================================================
