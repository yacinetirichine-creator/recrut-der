# ================================================
# 📚 GUIDE D'INTÉGRATION JOB BOARDS
# Indeed & LinkedIn
# ================================================

## 🔑 Obtenir les clés API

### 1️⃣ Indeed API

**Étapes:**
1. Créer un compte sur [Indeed Publisher](https://www.indeed.com/publishers)
2. Remplir le formulaire de demande d'API
3. Attendre l'approbation (1-2 jours)
4. Récupérer votre `Publisher ID` (= API Key)

**Documentation:**
- API Docs: https://opensource.indeedeng.io/api-documentation/
- Job Search API: https://opensource.indeedeng.io/api-documentation/docs/job-search/

**Limitations:**
- Gratuit jusqu'à 10,000 requêtes/mois
- Rate limit: 1 requête/seconde

---

### 2️⃣ LinkedIn Jobs API

**Étapes:**
1. Créer une app sur [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Demander l'accès à "LinkedIn Talent Solutions" (nécessite un compte entreprise)
3. Configurer OAuth 2.0 credentials
4. Récupérer `Client ID` et `Client Secret`

**Documentation:**
- API Docs: https://learn.microsoft.com/en-us/linkedin/talent/job-postings
- Authentication: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication

**Limitations:**
- Accès payant (LinkedIn Recruiter ou Talent Solutions requis)
- Rate limit: 100 requêtes/jour (tier gratuit)

---

## ⚙️ Configuration dans l'application

### Variables d'environnement

Créer un fichier `.env` à la racine du projet:

```bash
# Indeed API
INDEED_API_KEY=votre_publisher_id_ici

# LinkedIn API
LINKEDIN_CLIENT_ID=votre_client_id_ici
LINKEDIN_CLIENT_SECRET=votre_client_secret_ici
```

### Dans Supabase

Ajouter les variables dans **Settings > API > Environment variables**:
- `INDEED_API_KEY`
- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`

---

## 🚀 Utilisation de l'API

### 1. Lancer une synchronisation

**Endpoint:** `POST /api/job-boards/sync`

**Headers:**
```
Authorization: Bearer <votre_token_admin>
```

**Body:**
```json
{
  "sources": ["indeed", "linkedin"],
  "keywords": "développeur python",
  "location": "Paris",
  "limit": 100
}
```

**Réponse:**
```json
{
  "status": "sync_started",
  "message": "Job board synchronization started in background",
  "sources": ["indeed", "linkedin"],
  "check_status_at": "/job-boards/sync-logs"
}
```

---

### 2. Vérifier les logs de sync

**Endpoint:** `GET /api/job-boards/sync-logs`

**Réponse:**
```json
[
  {
    "id": "uuid",
    "source": "indeed",
    "status": "success",
    "total_fetched": 85,
    "total_imported": 72,
    "total_updated": 13,
    "total_errors": 0,
    "started_at": "2025-12-21T10:00:00Z",
    "completed_at": "2025-12-21T10:02:30Z"
  }
]
```

---

### 3. Lister les offres importées

**Endpoint:** `GET /api/job-boards/external`

**Query params:**
- `source`: indeed | linkedin
- `is_active`: true | false
- `limit`: 50 (default)
- `offset`: 0 (default)

**Réponse:**
```json
[
  {
    "id": "uuid",
    "source": "indeed",
    "external_id": "abc123",
    "titre": "Développeur Python Senior",
    "entreprise_nom": "TechCorp",
    "description": "...",
    "localisation": "Paris, France",
    "type_contrat": "CDI",
    "url_offre": "https://indeed.com/job/abc123",
    "imported_at": "2025-12-21T10:00:00Z",
    "is_active": true,
    "offre_id": null
  }
]
```

---

### 4. Convertir une offre externe en offre locale

**Endpoint:** `POST /api/job-boards/external/{job_id}/convert`

**Body:**
```json
{
  "entreprise_id": "uuid-de-votre-entreprise"
}
```

**Réponse:**
```json
{
  "status": "converted",
  "external_job_id": "uuid-offre-externe",
  "local_offer_id": "uuid-nouvelle-offre-locale",
  "message": "External job successfully converted to local offer"
}
```

---

### 5. Voir les statistiques

**Endpoint:** `GET /api/job-boards/stats`

**Réponse:**
```json
{
  "sources": [
    {
      "source": "indeed",
      "total_jobs": 150,
      "active_jobs": 140,
      "converted_to_local": 25
    },
    {
      "source": "linkedin",
      "total_jobs": 80,
      "active_jobs": 75,
      "converted_to_local": 12
    }
  ],
  "total_external_jobs": 230,
  "total_active": 215,
  "total_converted": 37
}
```

---

## 🔄 Workflow complet

1. **Admin** lance la sync via `POST /job-boards/sync`
2. L'app importe les offres dans `external_job_postings`
3. **Recruteurs** voient les offres via `GET /job-boards/external`
4. **Recruteur** convertit une offre intéressante via `POST /job-boards/external/{id}/convert`
5. L'offre devient une offre locale modifiable
6. Les **candidats** peuvent swiper sur cette offre

---

## 🎨 Mapping des compétences

Pour améliorer le matching, vous pouvez créer des mappings de compétences:

```sql
INSERT INTO skill_mappings (external_skill, internal_skill, source) VALUES
('Python', 'Python', NULL),
('React.js', 'React', NULL),
('Node.js', 'Node', NULL),
('Full Stack Developer', 'Développeur Full Stack', 'indeed');
```

Cela permet de normaliser les compétences importées vers votre système.

---

## 🔧 Automatisation (optionnel)

### Synchronisation automatique avec cron

Créer un script Python pour lancer la sync périodiquement:

```python
import httpx
import asyncio
from datetime import datetime

async def auto_sync():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/job-boards/sync",
            json={"sources": ["indeed", "linkedin"]},
            headers={"Authorization": "Bearer <admin_token>"}
        )
        print(f"Sync started at {datetime.now()}: {response.json()}")

asyncio.run(auto_sync())
```

Ajouter au crontab (tous les jours à 2h du matin):
```bash
0 2 * * * cd /path/to/recrutder && .venv/bin/python scripts/auto_sync_jobs.py
```

---

## ⚠️ Limitations et bonnes pratiques

### Indeed
- ✅ Gratuit et facile d'accès
- ⚠️ Rate limit strict (1 req/sec)
- ⚠️ Données parfois incomplètes (salaire, type contrat)

### LinkedIn
- ✅ Données de qualité
- ✅ Informations détaillées sur les entreprises
- ⚠️ Accès payant (LinkedIn Recruiter)
- ⚠️ Quotas limités

### Recommandations
1. Ne pas sync trop souvent (1x/jour suffit)
2. Filtrer les résultats par localisation et mots-clés
3. Vérifier manuellement les offres importées
4. Nettoyer régulièrement les offres inactives

---

## 🆘 Support

En cas de problème:
1. Vérifier les logs de sync dans `/job-boards/sync-logs`
2. Vérifier les variables d'environnement
3. Tester les clés API directement sur les portails Indeed/LinkedIn
4. Consulter la documentation officielle des APIs

---

## 📝 TODO - Futures améliorations

- [ ] Support Pôle Emploi API
- [ ] Support Welcome to the Jungle API
- [ ] Matching automatique IA entre offres externes et candidats
- [ ] Notifications auto quand nouvelles offres correspondent au profil
- [ ] Dashboard analytics des imports
