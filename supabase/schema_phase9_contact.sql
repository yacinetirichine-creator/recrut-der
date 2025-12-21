-- ================================================
-- 📊 PHASE 9: CONTACT DIRECT
-- Email, messagerie interne, rendez-vous visio
-- ================================================

-- Table: Logs d'emails envoyés
CREATE TABLE IF NOT EXISTS public.email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    recipient_id UUID REFERENCES public.utilisateurs(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'sent',  -- sent, failed, bounced
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_email_logs_sender ON public.email_logs(sender_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON public.email_logs(recipient_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent ON public.email_logs(sent_at DESC);

-- Table: Rendez-vous / Meetings
CREATE TABLE IF NOT EXISTS public.meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    
    -- Informations RDV
    title TEXT NOT NULL,
    description TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    
    -- Type de meeting
    meeting_type VARCHAR(20) DEFAULT 'video',  -- video, phone, in_person
    meeting_link TEXT,  -- Lien Zoom/Google Meet/Jitsi
    location TEXT,  -- Pour meetings en personne
    
    -- Statut
    status VARCHAR(20) DEFAULT 'pending',  -- pending, confirmed, cancelled, completed, rescheduled
    confirmed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meetings_organizer ON public.meetings(organizer_id);
CREATE INDEX IF NOT EXISTS idx_meetings_participant ON public.meetings(participant_id);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON public.meetings(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON public.meetings(status);

-- Table: Rappels de RDV
CREATE TABLE IF NOT EXISTS public.meeting_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.utilisateurs(id) ON DELETE CASCADE,
    remind_at TIMESTAMPTZ NOT NULL,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meeting_reminders_meeting ON public.meeting_reminders(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_user ON public.meeting_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_remind ON public.meeting_reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_sent ON public.meeting_reminders(sent);

-- Ajouter colonne pour marquer les messages envoyés par email
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'messages' AND column_name = 'envoye_par_email'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN envoye_par_email BOOLEAN DEFAULT false;
    END IF;
END $$;

-- ================================================
-- RLS POLICIES
-- ================================================

-- email_logs: Utilisateur peut voir ses propres logs
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS email_logs_user_policy ON public.email_logs;
CREATE POLICY email_logs_user_policy ON public.email_logs
    FOR SELECT
    USING (sender_id = auth.uid() OR recipient_id = auth.uid());

-- meetings: Utilisateur peut voir/modifier ses RDV
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS meetings_user_policy ON public.meetings;
CREATE POLICY meetings_user_policy ON public.meetings
    FOR ALL
    USING (organizer_id = auth.uid() OR participant_id = auth.uid());

-- meeting_reminders: Utilisateur peut voir ses rappels
ALTER TABLE public.meeting_reminders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS meeting_reminders_user_policy ON public.meeting_reminders;
CREATE POLICY meeting_reminders_user_policy ON public.meeting_reminders
    FOR ALL
    USING (user_id = auth.uid());

-- ================================================
-- FONCTIONS UTILITAIRES
-- ================================================

-- Fonction pour créer automatiquement des rappels de RDV
CREATE OR REPLACE FUNCTION create_meeting_reminders()
RETURNS TRIGGER AS $$
BEGIN
    -- Rappel 24h avant
    INSERT INTO public.meeting_reminders (meeting_id, user_id, remind_at)
    VALUES 
        (NEW.id, NEW.organizer_id, NEW.scheduled_at - INTERVAL '24 hours'),
        (NEW.id, NEW.participant_id, NEW.scheduled_at - INTERVAL '24 hours');
    
    -- Rappel 1h avant
    INSERT INTO public.meeting_reminders (meeting_id, user_id, remind_at)
    VALUES 
        (NEW.id, NEW.organizer_id, NEW.scheduled_at - INTERVAL '1 hour'),
        (NEW.id, NEW.participant_id, NEW.scheduled_at - INTERVAL '1 hour');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_create_meeting_reminders ON public.meetings;
CREATE TRIGGER trigger_create_meeting_reminders
    AFTER INSERT ON public.meetings
    FOR EACH ROW
    EXECUTE FUNCTION create_meeting_reminders();

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_meeting_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_meeting ON public.meetings;
CREATE TRIGGER trigger_update_meeting
    BEFORE UPDATE ON public.meetings
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_timestamp();

-- ================================================
-- VUES UTILES
-- ================================================

-- Vue: RDV à venir
CREATE OR REPLACE VIEW public.upcoming_meetings AS
SELECT 
    m.*,
    o.nom as organizer_name,
    o.email as organizer_email,
    p.nom as participant_name,
    p.email as participant_email
FROM public.meetings m
JOIN public.utilisateurs o ON m.organizer_id = o.id
JOIN public.utilisateurs p ON m.participant_id = p.id
WHERE m.scheduled_at > NOW()
  AND m.status NOT IN ('cancelled', 'completed')
ORDER BY m.scheduled_at ASC;

-- Vue: Stats emails
CREATE OR REPLACE VIEW public.email_stats AS
SELECT 
    DATE(sent_at) as date,
    status,
    COUNT(*) as total_emails
FROM public.email_logs
GROUP BY DATE(sent_at), status
ORDER BY date DESC;

-- Vue: Stats RDV
CREATE OR REPLACE VIEW public.meeting_stats AS
SELECT 
    DATE(scheduled_at) as date,
    meeting_type,
    status,
    COUNT(*) as total_meetings,
    AVG(duration_minutes) as avg_duration
FROM public.meetings
GROUP BY DATE(scheduled_at), meeting_type, status
ORDER BY date DESC;
