-- ================================================
-- 📋 MISE À JOUR SCHÉMA POUR PARSING IA DE FICHES DE POSTE
-- ================================================
-- Date: 21 décembre 2025
-- Version: v2.1
-- Description: Ajout des champs pour le parsing automatique
--              et le support multilingue des offres d'emploi
-- ================================================

-- 1. Ajouter les nouveaux champs à la table offres
-- ================================================

ALTER TABLE offres
ADD COLUMN IF NOT EXISTS description_courte TEXT,
ADD COLUMN IF NOT EXISTS ville TEXT,
ADD COLUMN IF NOT EXISTS pays TEXT DEFAULT 'France',
ADD COLUMN IF NOT EXISTS code_postal TEXT,
ADD COLUMN IF NOT EXISTS avantages TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS responsabilites TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS missions_principales TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS langue TEXT DEFAULT 'fr',
ADD COLUMN IF NOT EXISTS statut TEXT DEFAULT 'brouillon',
ADD COLUMN IF NOT EXISTS source_parsing TEXT,
ADD COLUMN IF NOT EXISTS parsed_metadata JSONB;

-- 2. Ajouter des commentaires pour documenter les champs
-- ================================================

COMMENT ON COLUMN offres.description_courte IS 'Résumé court de l''offre (2-3 phrases)';
COMMENT ON COLUMN offres.ville IS 'Ville du poste';
COMMENT ON COLUMN offres.pays IS 'Pays du poste (défaut: France)';
COMMENT ON COLUMN offres.code_postal IS 'Code postal du poste';
COMMENT ON COLUMN offres.avantages IS 'Liste des avantages (tickets restaurant, mutuelle, etc.)';
COMMENT ON COLUMN offres.responsabilites IS 'Liste des responsabilités du poste';
COMMENT ON COLUMN offres.missions_principales IS 'Liste des missions principales';
COMMENT ON COLUMN offres.langue IS 'Langue de l''offre (en, fr, es, de, zh, hi, ar, bn, ru, pt)';
COMMENT ON COLUMN offres.statut IS 'Statut de l''offre: brouillon, publiee, archivee, expiree';
COMMENT ON COLUMN offres.source_parsing IS 'Source du parsing: manual, ai_pdf, ai_text, ai_docx';
COMMENT ON COLUMN offres.parsed_metadata IS 'Métadonnées du parsing IA (langue détectée, fichier original, etc.)';

-- 3. Créer des index pour améliorer les performances
-- ================================================

-- Index sur la langue pour filtrer les offres par langue
CREATE INDEX IF NOT EXISTS idx_offres_langue ON offres(langue);

-- Index sur le statut pour filtrer les offres publiées/brouillons
CREATE INDEX IF NOT EXISTS idx_offres_statut ON offres(statut);

-- Index sur la ville pour la recherche géographique
CREATE INDEX IF NOT EXISTS idx_offres_ville ON offres(ville);

-- Index sur le pays pour le filtrage international
CREATE INDEX IF NOT EXISTS idx_offres_pays ON offres(pays);

-- Index GIN pour la recherche dans les avantages
CREATE INDEX IF NOT EXISTS idx_offres_avantages ON offres USING GIN (avantages);

-- Index GIN pour les métadonnées de parsing
CREATE INDEX IF NOT EXISTS idx_offres_parsed_metadata ON offres USING GIN (parsed_metadata);

-- 4. Créer un type enum pour les statuts d'offre (optionnel, pour plus de rigueur)
-- ================================================

DO $$ BEGIN
    CREATE TYPE statut_offre AS ENUM ('brouillon', 'publiee', 'archivee', 'expiree');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Si vous voulez utiliser l'enum, décommentez les lignes suivantes:
-- ALTER TABLE offres ALTER COLUMN statut TYPE statut_offre USING statut::statut_offre;

-- 5. Créer une vue pour les offres multilingues
-- ================================================

CREATE OR REPLACE VIEW offres_multilingues AS
SELECT 
    o.id,
    o.titre,
    o.description_courte,
    o.langue,
    o.statut,
    o.ville,
    o.pays,
    o.salaire_min,
    o.salaire_max,
    o.type_contrat,
    o.remote_possible,
    o.created_at,
    o.entreprise as entreprise_nom,
    COUNT(*) OVER (PARTITION BY o.titre, o.entreprise) as nb_traductions
FROM offres o
WHERE o.statut = 'publiee'
ORDER BY o.created_at DESC;

COMMENT ON VIEW offres_multilingues IS 'Vue des offres publiées avec comptage des traductions disponibles';

-- 6. Fonction pour obtenir toutes les traductions d'une offre
-- ================================================

CREATE OR REPLACE FUNCTION get_offre_traductions(offre_titre TEXT, entreprise_nom TEXT)
RETURNS TABLE (
    id UUID,
    langue TEXT,
    titre TEXT,
    description_courte TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.langue,
        o.titre,
        o.description_courte
    FROM offres o
    WHERE o.titre ILIKE '%' || offre_titre || '%'
      AND o.entreprise = get_offre_traductions.entreprise_nom
      AND o.statut = 'publiee'
    ORDER BY o.langue;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_offre_traductions IS 'Récupère toutes les traductions d''une offre d''emploi';

-- 7. Fonction pour obtenir les statistiques de parsing
-- ================================================

CREATE OR REPLACE FUNCTION stats_parsing_offres()
RETURNS TABLE (
    source_parsing TEXT,
    nombre_offres BIGINT,
    pourcentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(o.source_parsing, 'manual') as source_parsing,
        COUNT(*) as nombre_offres,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as pourcentage
    FROM offres o
    GROUP BY o.source_parsing
    ORDER BY nombre_offres DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION stats_parsing_offres IS 'Statistiques sur les méthodes de création d''offres (IA vs manuel)';

-- 8. Fonction pour obtenir les langues les plus utilisées
-- ================================================

CREATE OR REPLACE FUNCTION stats_langues_offres()
RETURNS TABLE (
    langue TEXT,
    nombre_offres BIGINT,
    pourcentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.langue,
        COUNT(*) as nombre_offres,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as pourcentage
    FROM offres o
    WHERE o.statut = 'publiee'
    GROUP BY o.langue
    ORDER BY nombre_offres DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION stats_langues_offres IS 'Statistiques sur les langues des offres publiées';

-- 9. Trigger pour valider la langue
-- ================================================

CREATE OR REPLACE FUNCTION validate_offre_langue()
RETURNS TRIGGER AS $$
BEGIN
    -- Vérifier que la langue est valide (parmi les 10 supportées)
    IF NEW.langue NOT IN ('en', 'zh', 'hi', 'es', 'fr', 'ar', 'bn', 'ru', 'pt', 'de') THEN
        RAISE EXCEPTION 'Langue non supportée: %. Langues valides: en, zh, hi, es, fr, ar, bn, ru, pt, de', NEW.langue;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_offre_langue
    BEFORE INSERT OR UPDATE ON offres
    FOR EACH ROW
    EXECUTE FUNCTION validate_offre_langue();

COMMENT ON TRIGGER trigger_validate_offre_langue ON offres IS 'Valide que la langue de l''offre est supportée';

-- 10. Trigger pour gérer les statuts
-- ================================================

CREATE OR REPLACE FUNCTION manage_offre_statut()
RETURNS TRIGGER AS $$
BEGIN
    -- Si l'offre est publiée pour la première fois, enregistrer la date
    IF NEW.statut = 'publiee' AND OLD.statut = 'brouillon' THEN
        NEW.updated_at = NOW();
    END IF;
    
    -- Si l'offre est archivée, vérifier qu'elle était publiée
    IF NEW.statut = 'archivee' AND OLD.statut != 'publiee' THEN
        RAISE EXCEPTION 'Seules les offres publiées peuvent être archivées';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_manage_offre_statut
    BEFORE UPDATE ON offres
    FOR EACH ROW
    EXECUTE FUNCTION manage_offre_statut();

COMMENT ON TRIGGER trigger_manage_offre_statut ON offres IS 'Gère les transitions de statuts des offres';

-- 11. Mettre à jour les politiques RLS (Row Level Security)
-- ================================================

-- Les recruteurs peuvent voir leurs brouillons
CREATE POLICY "Recruteurs peuvent voir leurs brouillons"
    ON offres FOR SELECT
    USING (
        statut = 'brouillon' AND 
        recruteur_id IN (
            SELECT id FROM recruteurs WHERE user_id = auth.uid()
        )
    );

-- Les candidats ne voient que les offres publiées
CREATE POLICY "Candidats voient offres publiées"
    ON offres FOR SELECT
    USING (statut = 'publiee');

-- Les recruteurs peuvent modifier leurs offres
CREATE POLICY "Recruteurs modifient leurs offres"
    ON offres FOR UPDATE
    USING (
        recruteur_id IN (
            SELECT id FROM recruteurs WHERE user_id = auth.uid()
        )
    );

-- 12. Créer une table pour historiser les traductions
-- ================================================

CREATE TABLE IF NOT EXISTS offres_traductions_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    offre_id UUID REFERENCES offres(id) ON DELETE CASCADE,
    langue_source TEXT NOT NULL,
    langue_cible TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    metadata JSONB
);

CREATE INDEX idx_traductions_history_offre ON offres_traductions_history(offre_id);
CREATE INDEX idx_traductions_history_langues ON offres_traductions_history(langue_source, langue_cible);

COMMENT ON TABLE offres_traductions_history IS 'Historique des traductions d''offres effectuées';

-- 13. Fonction pour enregistrer une traduction
-- ================================================

CREATE OR REPLACE FUNCTION record_translation(
    p_offre_id UUID,
    p_langue_source TEXT,
    p_langue_cible TEXT,
    p_metadata JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_translation_id UUID;
BEGIN
    INSERT INTO offres_traductions_history (
        offre_id,
        langue_source,
        langue_cible,
        created_by,
        metadata
    ) VALUES (
        p_offre_id,
        p_langue_source,
        p_langue_cible,
        auth.uid(),
        p_metadata
    )
    RETURNING id INTO v_translation_id;
    
    RETURN v_translation_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION record_translation IS 'Enregistre une traduction d''offre dans l''historique';

-- ================================================
-- FIN DE LA MIGRATION
-- ================================================

-- Vérification: Afficher les nouvelles colonnes
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'offres'
  AND column_name IN (
    'description_courte', 'ville', 'pays', 'code_postal',
    'avantages', 'responsabilites', 'missions_principales',
    'langue', 'statut', 'source_parsing', 'parsed_metadata'
  )
ORDER BY ordinal_position;

-- Afficher les index créés
SELECT 
    indexname, 
    indexdef
FROM pg_indexes
WHERE tablename = 'offres'
  AND indexname LIKE 'idx_offres_%'
ORDER BY indexname;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE '✅ Migration terminée avec succès !';
    RAISE NOTICE '📋 Nouveaux champs ajoutés à la table offres';
    RAISE NOTICE '🔍 Index créés pour optimiser les recherches';
    RAISE NOTICE '🔒 Politiques RLS mises à jour';
    RAISE NOTICE '📊 Fonctions de statistiques créées';
    RAISE NOTICE '🌍 Support multilingue activé (10 langues)';
END $$;
