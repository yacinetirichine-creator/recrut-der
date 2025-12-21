# 📄 Parsing Automatique de Fiches de Poste avec IA

## 🎯 Vue d'ensemble

Le système de parsing automatique de fiches de poste permet aux recruteurs de :

1. **Uploader une fiche de poste** (PDF, DOCX, TXT ou copier-coller)
2. **L'IA analyse et extrait** automatiquement toutes les informations
3. **Détection automatique** de la langue (parmi 10 langues supportées)
4. **Traduction optionnelle** dans la langue de votre choix
5. **Validation et modification** avant publication
6. **Suggestions d'amélioration** par l'IA

---

## 🌍 Langues Supportées (Top 10 Mondial)

| # | Code | Langue | Locuteurs |
|---|------|--------|-----------|
| 1 | `en` | 🇬🇧 English | 1.4 milliard |
| 2 | `zh` | 🇨🇳 中文 (Chinese) | 1.1 milliard |
| 3 | `hi` | 🇮🇳 हिन्दी (Hindi) | 600 millions |
| 4 | `es` | 🇪🇸 Español | 560 millions |
| 5 | `fr` | 🇫🇷 Français | 280 millions |
| 6 | `ar` | 🇸🇦 العربية (Arabic) | 274 millions |
| 7 | `bn` | 🇧🇩 বাংলা (Bengali) | 265 millions |
| 8 | `ru` | 🇷🇺 Русский (Russian) | 258 millions |
| 9 | `pt` | 🇵🇹 Português | 252 millions |
| 10 | `de` | 🇩🇪 Deutsch | 134 millions |

---

## 📋 Workflow Complet

### Option 1 : Upload de Fichier

```
Recruteur → Upload PDF/DOCX → IA Parse → Validation → Publication
```

**Endpoint:** `POST /api/job/upload-job-description`

**Formats supportés:**
- PDF (`.pdf`)
- Word (`.docx`)
- Texte (`.txt`)

**Paramètres:**
```json
{
  "file": "fichier_de_poste.pdf",
  "auto_detect_language": true,
  "target_language": "fr"
}
```

**Exemple de réponse:**
```json
{
  "success": true,
  "message": "Fiche de poste analysée avec succès",
  "langue_detectee": "en",
  "langue_sortie": "fr",
  "data": {
    "titre_poste": "Développeur Full Stack Senior",
    "entreprise": "TechStartup",
    "description_complete": "...",
    "description_courte": "...",
    "competences_requises": ["JavaScript", "React", "Node.js"],
    "competences_bonus": ["Docker", "Kubernetes"],
    "soft_skills_recherches": ["Communication", "Autonomie"],
    "experience_min": 5,
    "experience_max": 8,
    "salaire_min": 55000,
    "salaire_max": 70000,
    "localisation": "Paris",
    "ville": "Paris",
    "pays": "France",
    "remote_possible": true,
    "politique_teletravail": "hybride",
    "type_contrat": "cdi",
    "langues_requises": ["Français", "Anglais"],
    "avantages": ["Tickets restaurant", "Mutuelle", "RTT"]
  }
}
```

---

### Option 2 : Copier-Coller de Texte

```
Recruteur → Colle le texte → IA Parse → Validation → Publication
```

**Endpoint:** `POST /api/job/parse-job-text`

**Paramètres:**
```json
{
  "job_text": "Texte complet de la fiche de poste...",
  "auto_detect_language": true,
  "target_language": "fr"
}
```

---

## ✅ Validation et Création d'Offre

Une fois les données parsées, le recruteur peut :

1. **Accepter telles quelles** → Publication directe
2. **Modifier** certains champs → Puis publier
3. **Demander des suggestions** → Améliorer → Publier

**Endpoint:** `POST /api/job/validate-and-create-offer`

**Paramètres:**
```json
{
  "job_data": {
    "titre_poste": "Développeur Full Stack Senior",
    "entreprise": "TechStartup",
    // ... tous les champs parsés (modifiables)
  }
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Offre créée avec succès",
  "offre": {
    "id": 123,
    "titre": "Développeur Full Stack Senior",
    "statut": "publiee",
    // ... offre complète
  }
}
```

---

## 💡 Suggestions d'Amélioration

L'IA peut analyser votre fiche de poste et suggérer des améliorations.

**Endpoint:** `POST /api/job/improve-job-description`

**Paramètres:**
```json
{
  "job_data": {
    // ... données de la fiche de poste
  }
}
```

**Réponse:**
```json
{
  "success": true,
  "suggestions": {
    "score_qualite": 75,
    "points_forts": [
      "Description claire des responsabilités",
      "Salaire compétitif affiché",
      "Avantages bien détaillés"
    ],
    "suggestions_amelioration": [
      "Ajouter des informations sur la culture d'entreprise",
      "Préciser les opportunités d'évolution",
      "Mentionner les projets techniques intéressants"
    ],
    "description_amelioree": "Version optimisée de la description...",
    "description_courte_amelioree": "Résumé attractif...",
    "titres_alternatifs": [
      "Lead Developer Full Stack",
      "Architecte Web Full Stack"
    ],
    "mots_cles_seo": [
      "développeur full stack",
      "react",
      "node.js",
      "startup paris"
    ],
    "conseils_attraction_candidats": [
      "Mettre en avant les technologies modernes",
      "Souligner l'impact du poste"
    ]
  }
}
```

---

## 🌐 Traduction Multi-langue

Traduisez votre offre dans les 10 langues supportées pour toucher un public international.

**Endpoint:** `POST /api/job/translate-job-description`

**Paramètres:**
```json
{
  "job_data": {
    // ... fiche de poste en français
  },
  "target_language": "en"
}
```

**Exemple d'utilisation:**
```bash
# Publier la même offre en 3 langues
1. Version française (originale)
2. POST /translate → "en" → Version anglaise
3. POST /translate → "es" → Version espagnole
```

---

## 🔧 Configuration

### Variables d'environnement

Ajoutez dans votre fichier `.env` :

```bash
# IA Provider (choisir un des deux)
OPENAI_API_KEY=sk-...           # Pour OpenAI GPT-4
ANTHROPIC_API_KEY=sk-ant-...     # Pour Claude
```

### Coûts estimés

| Provider | Modèle | Coût par fiche |
|----------|--------|----------------|
| OpenAI | GPT-4o-mini | ~0.02-0.05€ |
| Anthropic | Claude Sonnet | ~0.04-0.08€ |

---

## 📊 Exemples d'Usage

### Exemple 1 : Fiche en français (upload PDF)

```python
import requests

files = {'file': open('fiche_poste.pdf', 'rb')}
data = {
    'auto_detect_language': True,
    'target_language': 'fr'
}

response = requests.post(
    'http://localhost:8000/api/job/upload-job-description',
    files=files,
    data=data,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

result = response.json()
print(f"Titre: {result['data']['titre_poste']}")
print(f"Langue détectée: {result['langue_detectee']}")
```

### Exemple 2 : Fiche en anglais, traduite en français

```python
job_text = """
SENIOR SOFTWARE ENGINEER
We are seeking a talented engineer...
"""

response = requests.post(
    'http://localhost:8000/api/job/parse-job-text',
    json={
        'job_text': job_text,
        'auto_detect_language': True,
        'target_language': 'fr'  # Traduit automatiquement
    },
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

result = response.json()
# Résultat traduit en français
print(f"Titre traduit: {result['data']['titre_poste']}")
```

### Exemple 3 : Validation et création

```python
# Après parsing, valider et créer l'offre
parsed_data = result['data']

# Le recruteur peut modifier les données ici
parsed_data['salaire_min'] = 60000  # Ajustement

response = requests.post(
    'http://localhost:8000/api/job/validate-and-create-offer',
    json={'job_data': parsed_data},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

offre = response.json()['offre']
print(f"Offre créée avec l'ID: {offre['id']}")
```

---

## 🎨 Interface Utilisateur (Recommandations)

### Écran 1 : Choix du mode de saisie

```
┌──────────────────────────────────────────────┐
│  Comment souhaitez-vous créer votre offre ?  │
├──────────────────────────────────────────────┤
│                                              │
│  📄  Upload de fichier                       │
│  (PDF, DOCX, TXT)                            │
│                                              │
│  📝  Copier-coller le texte                  │
│                                              │
│  ✍️   Saisie manuelle                         │
│                                              │
└──────────────────────────────────────────────┘
```

### Écran 2 : Résultats du parsing

```
┌──────────────────────────────────────────────┐
│  ✅ Fiche de poste analysée avec succès      │
├──────────────────────────────────────────────┤
│  🌍 Langue détectée: Anglais → Français      │
│                                              │
│  📋 Informations extraites:                  │
│                                              │
│  Titre: [Développeur Full Stack Senior]     │
│  Entreprise: [TechStartup]                   │
│  Salaire: [55k - 70k €]                      │
│  Expérience: [5 - 8 ans]                     │
│                                              │
│  Compétences requises: (4)                   │
│  ✓ JavaScript  ✓ React  ✓ Node.js  ✓ SQL    │
│                                              │
│  [Modifier]  [Accepter]  [Suggestions IA]    │
└──────────────────────────────────────────────┘
```

### Écran 3 : Suggestions d'amélioration

```
┌──────────────────────────────────────────────┐
│  💡 Suggestions d'amélioration               │
├──────────────────────────────────────────────┤
│  Score qualité: 75/100 🟡                    │
│                                              │
│  ✅ Points forts:                            │
│  • Description claire                        │
│  • Salaire transparent                       │
│                                              │
│  📝 À améliorer:                             │
│  • Ajouter la culture d'entreprise           │
│  • Détailler les opportunités d'évolution    │
│                                              │
│  [Appliquer les suggestions]  [Ignorer]      │
└──────────────────────────────────────────────┘
```

---

## 🔄 Workflow Frontend Recommandé

1. **Recruteur arrive sur "Créer une offre"**
   - 3 options : Upload / Copier-coller / Manuel

2. **Si Upload ou Copier-coller :**
   - Sélection de la langue cible (défaut: auto-detect)
   - Appel API → Parsing
   - Affichage résultats avec tous les champs pré-remplis
   - Chaque champ est **modifiable**

3. **Actions disponibles :**
   - ✏️ Modifier n'importe quel champ
   - 💡 Demander des suggestions IA
   - 🌐 Traduire dans une autre langue
   - ✅ Valider et publier

4. **Brouillon automatique**
   - L'offre est sauvegardée en statut "brouillon"
   - Le recruteur peut revenir modifier plus tard
   - Publication finale quand tout est validé

---

## 🚀 Test du Service

Pour tester le service de parsing :

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Exécuter le script de test
PYTHONPATH=/Users/yacinetirichine/Downloads/recrutder python scripts/test_job_parser.py
```

**Note:** Vous devez avoir une clé API (OpenAI ou Anthropic) dans votre `.env` pour les tests complets.

---

## 📝 Notes Importantes

1. **Toujours modifiable** : Même avec le parsing IA, le recruteur garde le contrôle total et peut modifier chaque champ

2. **Détection automatique** : La langue est détectée automatiquement, pas besoin de la spécifier

3. **Multi-publication** : Une fois l'offre validée, elle peut être publiée sur les job boards (Indeed, LinkedIn, etc.)

4. **Historique** : Toutes les offres parsées conservent les métadonnées du parsing dans `parsed_metadata`

5. **Confidentialité** : Les données ne sont envoyées à l'IA que pour le parsing, jamais stockées par OpenAI/Anthropic

---

## 🎯 Prochaines Étapes

- [ ] Ajouter support d'autres formats (HTML, RTF)
- [ ] Améliorer la détection des salaires en devises étrangères
- [ ] Ajouter la détection de biais dans les offres (langage inclusif)
- [ ] Générer automatiquement des images d'offre pour les réseaux sociaux
- [ ] A/B testing de différentes versions d'une même offre

---

## 📞 Support

Pour toute question sur cette fonctionnalité :
- Documentation complète : `/docs` de l'API
- Exemples de code : `scripts/test_job_parser.py`
- Tests : `tests/test_job_parser.py`
