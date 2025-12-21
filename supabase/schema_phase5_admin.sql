-- ═══════════════════════════════════════════════════════════════════
-- 🔧 PHASE 5: Dashboard Administrateur - Compléments SQL
-- ═══════════════════════════════════════════════════════════════════

-- Ajouter les champs de suspension aux candidats (si non existants)
ALTER TABLE candidats 
ADD COLUMN IF NOT EXISTS suspendu BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS raison_suspension TEXT,
ADD COLUMN IF NOT EXISTS suspendu_le TIMESTAMPTZ;

-- Ajouter les champs de suspension aux recruteurs
ALTER TABLE recruteurs 
ADD COLUMN IF NOT EXISTS suspendu BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS raison_suspension TEXT,
ADD COLUMN IF NOT EXISTS suspendu_le TIMESTAMPTZ;

-- Ajouter les champs de suspension aux offres
ALTER TABLE offres 
ADD COLUMN IF NOT EXISTS raison_suspension TEXT,
ADD COLUMN IF NOT EXISTS suspendue_le TIMESTAMPTZ;

-- Ajouter un champ role à la table utilisateurs pour distinguer les admins
ALTER TABLE utilisateurs 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- Créer un index pour les recherches rapides par role
CREATE INDEX IF NOT EXISTS idx_utilisateurs_role ON utilisateurs(role);

-- Commenter les tables et colonnes
COMMENT ON COLUMN candidats.suspendu IS 'Indique si le compte candidat est suspendu par un admin';
COMMENT ON COLUMN candidats.raison_suspension IS 'Raison de la suspension du compte';
COMMENT ON COLUMN candidats.suspendu_le IS 'Date et heure de la suspension';

COMMENT ON COLUMN recruteurs.suspendu IS 'Indique si le compte recruteur est suspendu par un admin';
COMMENT ON COLUMN recruteurs.raison_suspension IS 'Raison de la suspension du compte';
COMMENT ON COLUMN recruteurs.suspendu_le IS 'Date et heure de la suspension';

COMMENT ON COLUMN offres.raison_suspension IS 'Raison de la suspension de l''offre';
COMMENT ON COLUMN offres.suspendue_le IS 'Date et heure de la suspension de l''offre';

COMMENT ON COLUMN utilisateurs.role IS 'Rôle de l''utilisateur (user, admin, super_admin)';

-- ═══════════════════════════════════════════════════════════════════
-- 🔐 RLS Policies pour les admins
-- ═══════════════════════════════════════════════════════════════════

-- Supprimer les policies existantes si elles existent
DROP POLICY IF EXISTS "Admins peuvent tout lire dans candidats" ON candidats;
DROP POLICY IF EXISTS "Admins peuvent tout modifier dans candidats" ON candidats;
DROP POLICY IF EXISTS "Admins peuvent tout lire dans recruteurs" ON recruteurs;
DROP POLICY IF EXISTS "Admins peuvent tout modifier dans recruteurs" ON recruteurs;
DROP POLICY IF EXISTS "Admins peuvent tout lire dans offres" ON offres;
DROP POLICY IF EXISTS "Admins peuvent tout modifier dans offres" ON offres;
DROP POLICY IF EXISTS "Admins peuvent lire les logs" ON admin_logs;
DROP POLICY IF EXISTS "Admins peuvent créer des logs" ON admin_logs;

-- Policy pour permettre aux admins de tout lire dans candidats
CREATE POLICY "Admins peuvent tout lire dans candidats"
ON candidats FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

CREATE POLICY "Admins peuvent tout modifier dans candidats"
ON candidats FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

-- Mêmes policies pour recruteurs
CREATE POLICY "Admins peuvent tout lire dans recruteurs"
ON recruteurs FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

CREATE POLICY "Admins peuvent tout modifier dans recruteurs"
ON recruteurs FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

-- Policies pour les offres
CREATE POLICY "Admins peuvent tout lire dans offres"
ON offres FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

CREATE POLICY "Admins peuvent tout modifier dans offres"
ON offres FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

-- Policy pour admin_logs (lecture seule pour admins)
CREATE POLICY "Admins peuvent lire les logs"
ON admin_logs FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

CREATE POLICY "Admins peuvent créer des logs"
ON admin_logs FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM utilisateurs 
    WHERE utilisateurs.id = auth.uid() 
    AND utilisateurs.role = 'admin'
  )
);

-- ═══════════════════════════════════════════════════════════════════
-- 📊 Vues pour statistiques admin
-- ═══════════════════════════════════════════════════════════════════

-- Vue pour stats globales
CREATE OR REPLACE VIEW admin_stats_globales AS
SELECT 
  (SELECT COUNT(*) FROM candidats) as total_candidats,
  (SELECT COUNT(*) FROM candidats WHERE actif = TRUE) as candidats_actifs,
  (SELECT COUNT(*) FROM candidats WHERE suspendu = TRUE) as candidats_suspendus,
  (SELECT COUNT(*) FROM recruteurs) as total_recruteurs,
  (SELECT COUNT(*) FROM recruteurs WHERE actif = TRUE) as recruteurs_actifs,
  (SELECT COUNT(*) FROM recruteurs WHERE suspendu = TRUE) as recruteurs_suspendus,
  (SELECT COUNT(*) FROM offres) as total_offres,
  (SELECT COUNT(*) FROM offres WHERE publiee = TRUE) as offres_actives,
  (SELECT COUNT(*) FROM offres WHERE publiee = FALSE) as offres_inactives,
  (SELECT COUNT(*) FROM matchings) as total_matches,
  (SELECT COUNT(*) FROM swipes) as total_swipes,
  (SELECT COUNT(*) FROM swipes WHERE action = 'like') as total_likes,
  (SELECT COUNT(*) FROM support_tickets WHERE status = 'open') as tickets_ouverts,
  (SELECT COUNT(*) FROM support_tickets WHERE status = 'in_progress') as tickets_en_cours;

COMMENT ON VIEW admin_stats_globales IS 'Vue agrégée des statistiques principales pour le dashboard admin';

-- Vue pour activité récente (7 derniers jours)
CREATE OR REPLACE VIEW admin_activite_recente AS
SELECT 
  (SELECT COUNT(*) FROM candidats WHERE created_at >= NOW() - INTERVAL '7 days') as nouveaux_candidats_7j,
  (SELECT COUNT(*) FROM recruteurs WHERE created_at >= NOW() - INTERVAL '7 days') as nouveaux_recruteurs_7j,
  (SELECT COUNT(*) FROM offres WHERE created_at >= NOW() - INTERVAL '7 days') as nouvelles_offres_7j,
  (SELECT COUNT(*) FROM matchings WHERE created_at >= NOW() - INTERVAL '7 days') as nouveaux_matches_7j,
  (SELECT COUNT(*) FROM swipes WHERE created_at >= NOW() - INTERVAL '7 days') as swipes_7j;

COMMENT ON VIEW admin_activite_recente IS 'Activité des 7 derniers jours pour le dashboard admin';

-- ═══════════════════════════════════════════════════════════════════
-- ✅ Fin du script Phase 5
-- ═══════════════════════════════════════════════════════════════════

-- Afficher un message de confirmation
DO $$
BEGIN
  RAISE NOTICE '✅ Phase 5 - Dashboard Admin: Schéma mis à jour avec succès!';
  RAISE NOTICE '📊 Nouveaux champs ajoutés: suspendu, raison_suspension, suspendu_le';
  RAISE NOTICE '🔐 RLS Policies admin créées pour candidats, recruteurs, offres, logs';
  RAISE NOTICE '📈 Vues statistiques créées: admin_stats_globales, admin_activite_recente';
END $$;
