# 🔥 Phase 4: Matching IA Type Tinder - Documentation Complète

## ✅ Statut: TERMINÉ

### 📋 Résumé des Fonctionnalités

Phase 4 implémente un système de recommandations intelligent type Tinder avec:
- **Algorithme de scoring multi-critères avancé** (10 critères pondérés)
- **Feed de recommandations personnalisé** (70% top matches, 20% bons matches, 10% découverte)
- **Système de swipe** avec détection automatique des matchs
- **Explications détaillées** des scores de matching
- **Apprentissage des préférences** basé sur l'historique des swipes
- **Statistiques utilisateur** (taux de match, nombre de swipes, etc.)

---

## 🏗️ Architecture Technique

### Fichiers Créés

#### 1. `/api/services/tinder_matching.py` (450 lignes)
**Service principal de matching IA**

```python
class TinderMatchingEngine:
    """
    Moteur de matching type Tinder avec algorithme intelligent.
    """
```

**Fonctionnalités:**
- ✅ Calcul de score intelligent multi-critères
- ✅ Génération de feed personnalisé
- ✅ Apprentissage des préférences utilisateur
- ✅ Algorithme de diversification (pas toujours les mêmes profils)
- ✅ Bonus de fraîcheur pour nouveaux profils/offres
- ✅ Extraction automatique des points forts/faibles

**Critères de Matching (10 au total):**

| Critère | Poids par défaut | Description |
|---------|------------------|-------------|
| `competences_techniques` | 25% | Matching compétences requises + bonus |
| `experience` | 20% | Années d'expérience min/max avec pénalités |
| `qualifications` | 20% | Diplômes et certifications |
| `salaire` | 10% | Compatibilité fourchettes salariales |
| `localisation` | 10% | Distance + préférences remote |
| `secteur` | 5% | Secteur d'activité |
| `type_contrat` | 3% | CDI, CDD, freelance, etc. |
| `langues` | 3% | Langues requises |
| `soft_skills` | 2% | Compétences comportementales |
| `taille_entreprise` | 2% | Startup, PME, Grand groupe |

**Méthodes principales:**

```python
calculate_smart_score(candidat, offre, user_preferences, swipe_history)
# → Retourne score global + détails + explications + points forts/faibles

get_recommendation_feed(user_id, user_type, user_profile, all_candidates, all_offers, ...)
# → Génère feed intelligent avec diversification

_calculate_preference_adjustment(candidat, offre, swipe_history)
# → Ajuste score selon apprentissage des préférences (+10 points max)

_calculate_freshness_bonus(offre)
# → Bonus pour nouveaux contenus (+2 points)
```

---

#### 2. `/api/routes/tinder_feed.py` (450 lignes)
**Routes API pour le feed Tinder**

**Endpoints disponibles:**

##### GET `/api/tinder/feed`
Obtenir le feed de recommandations personnalisé

**Paramètres:**
- `limit` (query): Nombre de recommandations (1-50, défaut: 10)
- `authorization` (header): Bearer token JWT

**Comportement:**
- **Candidat** → Reçoit des offres d'emploi matchées
- **Recruteur** → Reçoit des profils de candidats matchés

**Algorithme de diversification:**
- 70% top matches (meilleurs scores)
- 20% bons matches (scores moyens-hauts)
- 10% découverte (aléatoire pour diversifier)

**Réponse (exemple candidat):**
```json
{
  "success": true,
  "count": 10,
  "user_type": "candidat",
  "recommendations": [
    {
      "id": "uuid",
      "titre": "Développeur Full Stack",
      "entreprise": "Tech Corp",
      "salaire_min": 45000,
      "salaire_max": 60000,
      "localisation": "Paris",
      "match_score": 87.3,
      "match_data": {
        "score_global": 87.3,
        "scores_detailles": {
          "competences": {"score": 90, "detail": "8/10 requises", "manquantes": ["Docker"], "bonus": ["React"]},
          "experience": {"score": 100, "detail": "5 ans (demandé: 3-7)"},
          "salaire": {"score": 100, "detail": "Fourchettes compatibles"},
          "localisation": {"score": 95, "detail": "Remote OK"},
          ...
        },
        "niveau_match": "🔥 Excellent Match",
        "explication": "Match basé principalement sur: competences: 90%, experience: 100%, localisation: 95%",
        "points_forts": ["competences", "experience", "salaire", "localisation"],
        "points_amelioration": ["taille_entreprise"]
      }
    },
    ...
  ]
}
```

---

##### GET `/api/tinder/match-detail/{item_id}`
Obtenir le détail d'un match potentiel avec explications complètes

**Paramètres:**
- `item_id` (path): UUID de l'offre (candidat) ou du candidat (recruteur)
- `authorization` (header): Bearer token JWT

**Réponse:**
```json
{
  "success": true,
  "type": "offre",
  "item": { /* Détails complets de l'offre */ },
  "match_data": {
    "score_global": 87.3,
    "scores_detailles": { /* 10 critères détaillés */ },
    "niveau_match": "🔥 Excellent Match",
    "explication": "Match basé principalement sur: ...",
    "points_forts": ["competences", "experience", ...],
    "points_amelioration": ["taille_entreprise"]
  }
}
```

**Utilité:** Afficher une page de détails avant de swiper, expliquer POURQUOI ce profil/offre correspond.

---

##### POST `/api/tinder/swipe`
Swiper sur un profil/offre (like ou dislike)

**Paramètres:**
- `item_id` (query): UUID de l'offre/candidat
- `action` (query): `"like"` ou `"dislike"`
- `authorization` (header): Bearer token JWT

**Comportement:**
1. Enregistre le swipe dans la table `swipes`
2. Si `action=like`, vérifie si l'autre partie a aussi liké
3. Si match mutuel → Le trigger SQL `check_and_create_match()` crée automatiquement le match
4. Retourne `is_match: true` si c'est un match

**Réponse (match):**
```json
{
  "success": true,
  "action": "like",
  "is_match": true,
  "message": "🎉 C'EST UN MATCH!",
  "swipe": { /* Données du swipe créé */ }
}
```

**Réponse (pas de match):**
```json
{
  "success": true,
  "action": "like",
  "is_match": false,
  "message": "Swipe enregistré"
}
```

---

##### GET `/api/tinder/stats`
Obtenir les statistiques de matching de l'utilisateur

**Réponse:**
```json
{
  "success": true,
  "user_type": "candidat",
  "stats": {
    "total_swipes": 45,
    "total_likes": 28,
    "total_dislikes": 17,
    "total_matches": 12,
    "match_rate": 42.9
  }
}
```

**Calculs:**
- `match_rate` = (total_matches / total_likes) * 100
- Stats agrégées sur toutes les offres pour les recruteurs

---

### 🔄 Modifications Apportées

#### `/api/main.py`
**Ajout de l'import:**
```python
from api.routes import ..., tinder_feed
```

**Enregistrement de la route:**
```python
app.include_router(tinder_feed.router, prefix="/api/tinder", tags=["🔥 Tinder Feed IA"])
```

---

## 🧪 Tests et Utilisation

### 1. Démarrer le serveur
```bash
cd /Users/yacinetirichine/Downloads/recrutder
source .venv/bin/activate
python run.py
```

### 2. Accéder à la documentation Swagger
**URL:** http://localhost:8000/docs

**Section:** `🔥 Tinder Feed IA`

### 3. Scénario de test complet

#### Étape 1: Créer un compte candidat
```bash
POST /api/auth/register
{
  "email": "candidat@test.fr",
  "password": "Test1234!",
  "nom": "Dupont",
  "prenom": "Jean",
  "type_utilisateur": "candidat",
  "telephone": "0601020304"
}
```

**Récupérer le `access_token`**

#### Étape 2: Obtenir le feed personnalisé
```bash
GET /api/tinder/feed?limit=10
Authorization: Bearer <access_token>
```

#### Étape 3: Voir le détail d'une offre
```bash
GET /api/tinder/match-detail/{offre_id}
Authorization: Bearer <access_token>
```

#### Étape 4: Swiper
```bash
POST /api/tinder/swipe?item_id={offre_id}&action=like
Authorization: Bearer <access_token>
```

#### Étape 5: Vérifier les stats
```bash
GET /api/tinder/stats
Authorization: Bearer <access_token>
```

---

## 🎯 Algorithme de Matching Détaillé

### 1. Calcul du Score Global

```
score_global = Σ (score_critère × poids_critère / 100)

Exemple:
- competences: 90 × 0.25 = 22.5
- experience: 100 × 0.20 = 20.0
- qualifications: 80 × 0.20 = 16.0
- salaire: 100 × 0.10 = 10.0
- localisation: 95 × 0.10 = 9.5
- secteur: 100 × 0.05 = 5.0
- type_contrat: 100 × 0.03 = 3.0
- langues: 100 × 0.03 = 3.0
- soft_skills: 70 × 0.02 = 1.4
- taille_entreprise: 50 × 0.02 = 1.0

Total = 91.4/100
```

### 2. Ajustements

**Apprentissage des préférences (+10 max):**
- Analyse des 50 derniers swipes
- Détecte les patterns (ex: user like souvent les startups)
- Ajuste le score si le profil/offre match le pattern

**Bonus fraîcheur (+2 fixe):**
- Offres/profils créés récemment
- Encourage la découverte de nouveaux contenus

### 3. Algorithme de Feed

```python
# 1. Filtrer les déjà swipés
items = [item for item in all_items if item.id not in already_swiped]

# 2. Calculer score pour chaque item
scored_items = [(item, calculate_smart_score(item)) for item in items]

# 3. Trier par score décroissant
scored_items.sort(key=lambda x: x[1], reverse=True)

# 4. Diversifier (pas QUE les meilleurs)
top_70% = scored_items[:int(limit * 0.7)]          # Top matches
good_20% = random.sample(scored_items[top:], 20%)   # Bons matches
discover_10% = random.sample(scored_items[rest:], 10%)  # Découverte

# 5. Mélanger légèrement
recommendations = shuffle(top_70% + good_20% + discover_10%)

return recommendations[:limit]
```

**Raison de la diversification:**
- Évite la monotonie (toujours les mêmes profils)
- Permet la découverte de profils "outsiders"
- Améliore l'engagement utilisateur

---

## 🎨 Niveaux de Match

| Score | Niveau | Emoji | Description |
|-------|--------|-------|-------------|
| 85-100 | Excellent Match | 🔥 | Correspondance quasi-parfaite |
| 70-84 | Très bon match | ✨ | Forte compatibilité |
| 55-69 | Bon match | 👍 | Bonne adéquation |
| 40-54 | Match moyen | 🤔 | Adéquation partielle |
| 0-39 | Faible match | ❌ | Peu compatible |

---

## 🔮 Évolutions Futures Possibles

### Machine Learning Avancé
- Remplacer `_calculate_preference_adjustment()` par un vrai modèle ML
- TensorFlow ou scikit-learn pour prédictions plus précises
- Clustering des utilisateurs par profil type

### Personnalisation des Poids
```python
# Permettre à l'utilisateur d'ajuster les poids
user_preferences = {
    "weights": {
        "competences_techniques": 30,  # +5% (plus important pour lui)
        "salaire": 15,                  # +5% (salaire prioritaire)
        "localisation": 5,              # -5% (moins important)
        ...
    }
}
```

### Boost Premium
```python
# Système de boost pour apparaître en priorité
if offre.has_boost:
    score_global += 20  # Apparaît en haut du feed
```

### Filtres Avancés
```python
GET /api/tinder/feed?min_score=70&remote_only=true&max_distance=50km
```

### Notifications Intelligentes
```python
# Notifier quand un profil très compatible apparaît
if score > 90:
    send_notification("🔥 Nouveau match parfait disponible!")
```

---

## 📊 Métriques de Performance

### Complexité Algorithmique

- **Calcul d'un score:** O(1) - Constant (10 critères fixes)
- **Génération du feed:** O(n log n) - Tri des items
- **Optimisation possible:** Caching des scores calculés

### Temps de Réponse Estimés

| Opération | Nb items | Temps estimé |
|-----------|----------|--------------|
| `calculate_smart_score()` | 1 | ~5ms |
| `get_recommendation_feed()` | 100 | ~50ms |
| `get_recommendation_feed()` | 1000 | ~500ms |

**Optimisations futures:**
- Indexation PostgreSQL sur champs critères
- Redis pour cache des scores
- Pagination pour grands volumes

---

## ✅ Checklist Phase 4

- [x] Service `TinderMatchingEngine` créé
- [x] Algorithme de scoring multi-critères (10 critères)
- [x] Génération de feed intelligent avec diversification
- [x] Apprentissage simple des préférences
- [x] Routes API `/feed`, `/match-detail`, `/swipe`, `/stats`
- [x] Gestion candidat + recruteur
- [x] Détection automatique des matchs (via trigger SQL)
- [x] Explications détaillées des scores
- [x] Points forts/faibles extraits automatiquement
- [x] Documentation complète
- [x] Serveur démarré et testé
- [x] Swagger documentation mise à jour

---

## 🚀 Prochaine Étape

**Phase 5: Dashboard Administrateur**
- Vue d'ensemble avec KPIs
- Gestion des utilisateurs (modération, suspension)
- Gestion des contenus (offres, profils)
- Système de support et tickets
- Logs et audit trail

---

## 📝 Notes Techniques

### Gestion de l'Authentification
Route `tinder_feed.py` utilise une authentification simplifiée:
```python
async def get_current_user(authorization: str = Header(...)):
    # Évite dépendances circulaires avec auth_service
    token = authorization.replace("Bearer ", "")
    user = supabase.auth.get_user(token)
    return {"id": user.user.id, "email": user.user.email}
```

### Triggers SQL Utilisés
- `check_and_create_match()` - Crée automatiquement un match quand 2 parties likent
- `update_conversation_last_message()` - Met à jour les conversations

### Dépendances Ajoutées
```bash
pip install loguru  # Logging amélioré (déjà installé)
```

---

**Date de création:** 21 décembre 2025  
**Statut:** ✅ Production Ready  
**Version:** v2.0
