# 🎯 Recrut'der - Plateforme de Matching IA pour le Recrutement

> "Le Tinder du recrutement" - Matching intelligent entre candidats et offres d'emploi

## 📋 Description

Recrut'der est une API de matching IA qui connecte les candidats aux offres d'emploi les plus pertinentes grâce à un algorithme de scoring multi-critères.

## 🚀 Démarrage Rapide (Mac)

```bash
# 1. Créer un environnement virtuel
python3 -m venv venv

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'API
python run.py
```

### Accéder à l'API

- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/docs
- **Documentation ReDoc** : http://localhost:8000/redoc

## 📁 Structure du Projet

```
recrutder/
├── api/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── routes/
│   │   ├── candidats.py     # Endpoints candidats
│   │   ├── offres.py        # Endpoints offres
│   │   └── matching.py      # Endpoints matching IA
│   ├── models/
│   │   ├── candidat.py      # Modèle candidat
│   │   ├── offre.py         # Modèle offre
│   │   └── matching.py      # Modèle résultat matching
│   ├── services/
│   │   └── matching_engine.py  # Moteur IA de matching
│   └── database/
│       └── fake_data.py     # Données de test
├── tests/
│   └── test_matching.py     # Tests unitaires
├── .vscode/                 # Config VS Code
├── requirements.txt
├── run.py                   # Script de démarrage
└── README.md
```

## 🔧 Configuration des Poids de Matching

Les poids sont configurables dans `api/services/matching_engine.py` :

| Catégorie | Critère | Poids |
|-----------|---------|-------|
| **Primordial** | Compétences techniques | 25% |
| **Primordial** | Expérience | 25% |
| **Primordial** | Qualifications | 25% |
| **Important** | Salaire | 8% |
| **Important** | Localisation | 7% |
| **Complémentaire** | Secteur, contrat, langues... | 10% |

## 📡 Endpoints API

### Candidats
- `GET /api/candidats` - Liste tous les candidats
- `GET /api/candidats/{id}` - Détail d'un candidat
- `POST /api/candidats` - Créer un candidat
- `PUT /api/candidats/{id}` - Modifier un candidat
- `DELETE /api/candidats/{id}` - Supprimer un candidat

### Offres
- `GET /api/offres` - Liste toutes les offres
- `GET /api/offres/{id}` - Détail d'une offre
- `POST /api/offres` - Créer une offre
- `PUT /api/offres/{id}` - Modifier une offre
- `DELETE /api/offres/{id}` - Supprimer une offre

### Matching IA
- `POST /api/matching/score` - Calculer le score entre 1 candidat et 1 offre
- `GET /api/matching/candidat/{id}/top-offres` - Top offres pour un candidat
- `GET /api/matching/offre/{id}/top-candidats` - Top candidats pour une offre
- `GET /api/matching/matrice` - Matrice complète de matching

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests verbeux
pytest -v
```

## 📊 Exemple de Réponse Matching

```json
{
  "score_global": 93.8,
  "niveau": "excellent",
  "recommandation": "🟢 EXCELLENT MATCH - Profil idéal !",
  "scores_details": {
    "competences_techniques": {"score": 90.0, "detail": "4/4 requises"},
    "experience": {"score": 100.0, "detail": "3 ans ✓"},
    "qualifications": {"score": 90.0, "detail": "1/1 requises"}
  }
}
```

## 🛠️ Développement

### Lancer en mode développement (rechargement auto)
```bash
uvicorn api.main:app --reload
```

### Debug avec VS Code
Appuyer sur `F5` et choisir "Python: FastAPI"

---

**Version**: 2.0 MVP  
**Auteur**: Yacine  
**Projet**: Recrut'der
