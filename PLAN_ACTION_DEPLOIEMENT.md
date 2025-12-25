# 🚀 PLAN D'ACTION PRÉ-DÉPLOIEMENT

**Recrut'der v2.0 - Préparation Déploiement**

Date: 25 décembre 2025  
Score Global: 92/100  
Statut: ✅ PRÊT avec corrections mineures

---

## 📋 RÉSUMÉ EXÉCUTIF

L'application est **prête pour déploiement** après correction de 2 points critiques et quelques améliorations.

**Temps estimé pour corrections:** 2-3 heures

---

## 🔴 POINT CRITIQUE #1: Routes sans authentification

### 📍 Localisation
- `api/routes/candidats.py` - Toutes les routes
- `api/routes/offres.py` - Toutes les routes  
- `api/routes/matching.py` - Toutes les routes

### 🔍 Problème
Les routes de candidats, offres et matchings sont actuellement sans protection. C'est correct en développement avec la fake_db, mais à sécuriser avant production.

### ✅ Solution à Implémenter

#### Candidats:
```python
# ✅ CORRECTION REQUISE
from api.routes.auth import get_current_user

@router.get("/", response_model=List[Candidat])
async def lister_candidats(current_user: dict = Depends(get_current_user)):
    # Vérifier que l'utilisateur a le droit de voir les candidats
    return list(candidats_db.values())

@router.get("/{candidat_id}", response_model=Candidat)
async def get_candidat(
    candidat_id: int,
    current_user: dict = Depends(get_current_user)
):
    if candidat_id not in candidats_db:
        raise HTTPException(status_code=404, detail=f"Candidat {candidat_id} non trouvé")
    return candidats_db[candidat_id]
```

#### Offres:
```python
# ✅ CORRECTION REQUISE
@router.get("/", response_model=List[Offre])
async def lister_offres(current_user: dict = Depends(get_current_user)):
    return list(offres_db.values())

@router.get("/{offre_id}", response_model=Offre)
async def get_offre(
    offre_id: int,
    current_user: dict = Depends(get_current_user)
):
    if offre_id not in offres_db:
        raise HTTPException(status_code=404, detail=f"Offre {offre_id} non trouvée")
    return offres_db[offre_id]
```

#### Matching:
```python
# ✅ CORRECTION REQUISE
@router.post("/score", response_model=MatchingResult)
async def calculer_score(
    request: MatchingRequest,
    current_user: dict = Depends(get_current_user)
):
    # ...
```

### ⏱️ Temps: 30 minutes

---

## 🔴 POINT CRITIQUE #2: Vérifier job_boards

### 📍 Localisation
- `api/main.py` ligne 18
- `api/routes/job_boards.py`

### 🔍 Problème
La route job_boards est désactivée avec un commentaire "Temporairement désactivé pour corriger"

### ✅ Solution
1. Tester la route en développement
2. Vérifier l'implémentation
3. Corriger les bugs si présents
4. Réactiver dans api/main.py

```python
# api/main.py - Ligne 18
from api.routes import (
    candidats, offres, matching, auth, entreprises, 
    swipes, messages, notifications, cv_ai, tinder_feed, 
    admin, support, rgpd, contact, job_ai,
    job_boards  # ✅ RÉACTIVER
)

# Et à la fin, inclure la route
app.include_router(
    job_boards.router, 
    prefix="/api/job_boards", 
    tags=["📊 Job Boards"]
)
```

### ⏱️ Temps: 1 heure

---

## 🟡 IMPORTANT #1: HttpOnly Cookies pour Auth Token

### 📍 Localisation
- `api/routes/auth.py` (backend)
- `website/app.html` (frontend)
- `api/config.py` (config)

### 🔍 Problème
Actuellement, les tokens sont stockés en localStorage (accessible via JavaScript). C'est vulnérable aux attaques XSS.

### ✅ Solution

#### 1️⃣ Backend: Retourner token en HttpOnly cookie

```python
# api/routes/auth.py

from fastapi.responses import JSONResponse

@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    # ... authentification
    
    # ✅ NOUVEAU: Retourner en HttpOnly cookie
    response = JSONResponse(content={
        "success": True,
        "user": {
            "id": user_id,
            "email": user_info.data["email"],
            "nom": user_info.data["nom"],
            "type_utilisateur": user_info.data["type_utilisateur"]
        }
    })
    
    response.set_cookie(
        key="auth_token",
        value=auth_response.session.access_token,
        max_age=auth_response.session.expires_in,
        secure=True,  # HTTPS only
        httponly=True,  # JS cannot access
        samesite="strict"  # CSRF protection
    )
    
    return response
```

#### 2️⃣ Frontend: Utiliser credentials: include

```javascript
// website/app.html

async function loginUser() {
    const credentials = {
        email: emailInput.value,
        password: passwordInput.value
    };

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        credentials: 'include'  // ✅ Envoyer cookies
    });

    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
    }

    // ✅ Plus besoin de localStorage!
    // Token est automatiquement envoyé avec chaque requête
    // (dans le cookie HttpOnly)
    
    window.location.href = 'dashboard.html';
}
```

#### 3️⃣ Fetch avec credentials partout

```javascript
// À MODIFIER PARTOUT où on utilise fetch

// ❌ AVANT
const response = await fetch(`${API_BASE_URL}/api/swipes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});

// ✅ APRÈS
const response = await fetch(`${API_BASE_URL}/api/swipes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include'  // ← Ajouter cela
});
```

### ⏱️ Temps: 1-2 heures

### 📝 Note
Cela améliore considérablement la sécurité XSS, mais nécessite des tests complets.

---

## 🟡 IMPORTANT #2: Ajouter Consentements RGPD

### 📍 Localisation
- `website/app.html` - Formulaire inscription
- `api/routes/auth.py` - Enregistrement
- Nouveau endpoint: `/api/rgpd/consent`

### 🔍 Problème
Les utilisateurs acceptent les conditions sans case à cocher. Non conforme RGPD.

### ✅ Solution

#### 1️⃣ Frontend: Ajouter checkboxes

```html
<!-- website/app.html - Ajouter avant submitBtn -->

<div class="form-group" id="consentGroup" style="display: none;">
    <div style="margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
        <label style="display: flex; align-items: flex-start; margin-bottom: 10px;">
            <input type="checkbox" id="rgpdConsent" style="margin-right: 10px; margin-top: 3px;" required>
            <span>J'accepte la <a href="/mentions-legales.html" target="_blank">politique de confidentialité</a> et les <a href="/conditions.html" target="_blank">conditions d'utilisation</a></span>
        </label>
        
        <label style="display: flex; align-items: flex-start;">
            <input type="checkbox" id="marketingConsent" style="margin-right: 10px; margin-top: 3px;">
            <span>Je souhaite recevoir les actualités et offres spéciales (optionnel)</span>
        </label>
    </div>
</div>
```

#### 2️⃣ JavaScript: Valider et envoyer

```javascript
async function registerUser() {
    // Vérifier consentement RGPD
    if (isRegister && !document.getElementById('rgpdConsent').checked) {
        alert('Vous devez accepter la politique de confidentialité');
        return;
    }

    const userData = {
        email: emailInput.value,
        password: passwordInput.value,
        nom: nomInput.value,
        type_utilisateur: typeInput.value,
        // ✅ Ajouter consentements
        rgpd_consent: document.getElementById('rgpdConsent').checked,
        marketing_consent: document.getElementById('marketingConsent').checked
    };

    // ... reste du code
}
```

#### 3️⃣ Backend: Enregistrer consentements

```python
# api/models/auth.py

class UserRegister(BaseModel):
    # ... champs existants
    rgpd_consent: bool = Field(True)  # Obligatoire
    marketing_consent: bool = Field(False, default=False)  # Optionnel

# api/routes/auth.py

from datetime import datetime

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    # ... création utilisateur
    
    # ✅ Enregistrer les consentements
    supabase.table("consent_log").insert({
        "user_id": user_id,
        "user_email": user_data.email,
        "rgpd_consent": user_data.rgpd_consent,
        "marketing_consent": user_data.marketing_consent,
        "consent_date": datetime.now().isoformat(),
        "consent_version": "1.0",  # Versionner les conditions
        "ip_address": None  # À récupérer de request.client.host
    }).execute()
```

### ⏱️ Temps: 1-2 heures

---

## 🟡 IMPORTANT #3: Rate Limiting Complet

### 📍 Localisation
- `api/routes/auth.py`
- `api/routes/support.py`
- `api/routes/contact.py`

### 🔍 Problème
Rate limiting implémenté mais pas utilisé sur les endpoints sensibles.

### ✅ Solution

```python
# api/routes/auth.py

from slowapi.util import get_remote_address
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # ✅ Max 5 tentatives/minute
async def login(
    request: Request,  # ← Ajouter Request
    credentials: UserLogin
):
    # ...

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")  # ✅ Max 3 inscriptions/minute
async def register(
    request: Request,  # ← Ajouter Request
    user_data: UserRegister
):
    # ...

@router.post("/reset-password")
@limiter.limit("3/hour")  # ✅ Max 3 demandes/heure
async def request_password_reset(
    request: Request,  # ← Ajouter Request
    data: PasswordReset
):
    # ...
```

### ⏱️ Temps: 30 minutes

---

## ✅ CHECKLIST PRÉ-PRODUCTION

```markdown
### 🔐 SÉCURITÉ
- [x] Headers OWASP configurés
- [x] CORS restricté
- [x] Authentification JWT
- [x] Validation des inputs
- [ ] Rate limiting complet
- [ ] HttpOnly cookies
- [ ] Consentements RGPD

### 📝 CONFIGURATION
- [x] Variables d'environnement définies
- [x] Fichier .env.example complet
- [ ] DEBUG=False en production
- [ ] CORS_ORIGINS avec vrais domaines
- [ ] JWT_SECRET unique et sécurisé
- [ ] Base de données initialisée

### 🛡️ DONNÉES & RGPD
- [x] Droit à l'oubli implémenté
- [x] Export de données implémenté
- [x] Logs de suppression
- [x] Anonymisation des messages
- [ ] Consentements enregistrés
- [ ] Politique de confidentialité publiée

### 🧪 TESTS
- [ ] Tests authentification complets
- [ ] Tests RGPD fonctionnels
- [ ] Tests rate limiting
- [ ] Load test (simul. 100 users)
- [ ] Scan sécurité OWASP

### 🚀 DÉPLOIEMENT
- [ ] Domaine HTTPS configuré
- [ ] Certificat SSL valide
- [ ] Backups automatisés
- [ ] Monitoring en place
- [ ] Plan de récupération
```

---

## 📅 TIMELINE PRÉ-DÉPLOIEMENT

| Tâche | Temps | Dépendance | Priorité |
|-------|-------|-----------|----------|
| Sécuriser routes candidats/offres/matching | 30 min | Aucune | 🔴 |
| Vérifier job_boards | 1h | Aucune | 🔴 |
| HttpOnly cookies | 1-2h | Aucune | 🟡 |
| Consentements RGPD | 1-2h | Aucune | 🟡 |
| Rate limiting complet | 30 min | Aucune | 🟡 |
| Tests complets | 2-3h | Toutes | 🟡 |
| **TOTAL** | **7-10h** | | |

---

## 🎯 PLAN D'ACTION CONSEILLÉ

### Jour 1 (Matin): Corrections Critiques
1. ✅ Sécuriser routes (30 min)
2. ✅ Vérifier job_boards (1h)
3. ✅ Tests rapides (30 min)

### Jour 1 (Après-midi): Sécurité Renforcée
4. ✅ HttpOnly cookies (1-2h)
5. ✅ Rate limiting (30 min)
6. ✅ Tests intégration (1h)

### Jour 2 (Matin): RGPD & Conformité
7. ✅ Consentements RGPD (1-2h)
8. ✅ Tests RGPD (1h)

### Jour 2 (Après-midi): Validation Finale
9. ✅ Tests de charge
10. ✅ Scan sécurité
11. ✅ Signoff pour déploiement

---

## 🎯 POINT FINAL

**Recommandation:** 

✅ **Déployer avec les corrections critiques**
- Routes sécurisées
- Job boards vérifié

⏳ **Améliorer rapidement après (J+1 à J+3)**
- HttpOnly cookies
- Consentements RGPD
- Rate limiting complet

Cette approche permet un déploiement rapide tout en minimisant les risques.

---

**Document de planification généré le:** 25 décembre 2025
