# 🚀 Recrut'der - Guide de Démarrage Rapide
> Démarrez en 3 minutes avec les nouvelles améliorations de sécurité

---

## ⚡ Démarrage Ultra-Rapide

### 1️⃣ Installer les dépendances

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les nouvelles dépendances (rate limiting)
pip install -r requirements.txt
```

### 2️⃣ Lancer l'API

```bash
# Démarrer l'API sur http://localhost:8000
python run.py
```

✅ **Vérifications automatiques** :
- Headers de sécurité activés
- Rate limiting configuré
- CORS strict appliqué
- 101 routes disponibles

### 3️⃣ Lancer le site web

```bash
# Dans un nouveau terminal
cd website
python3 -m http.server 8001
```

✅ **Accès** :
- 🌐 Site : http://localhost:8001/index.html
- 🤖 Chatbot IA : Automatiquement chargé dans toutes les pages
- 📱 Responsive : Testez sur mobile

---

## 🧪 Tester les Améliorations

### Test de sécurité complet

```bash
python scripts/test_security.py
```

**Résultat attendu** :
```
✅ Tests réussis: 6/6
🎉 Tous les tests sont passés avec succès!
```

### Test des headers HTTP

```bash
curl -I http://localhost:8000/health
```

**Headers de sécurité visibles** :
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
...
```

### Test du chatbot IA

1. Ouvrir http://localhost:8001/index.html
2. Cliquer sur le bouton 🤖 en bas à droite
3. Tester dans différentes langues (sélecteur en haut)
4. Envoyer un message (ex: "Comment fonctionne le matching?")

**Langues disponibles** : EN, FR, ES, DE, AR, ZH, PT, RU, HI, BN

---

## 📊 Endpoints Principaux

### API Documentation
- 📚 Swagger UI : http://localhost:8000/docs
- 📖 ReDoc : http://localhost:8000/redoc

### Health Check
```bash
curl http://localhost:8000/health
```

### Authentification
```bash
# Inscription
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "nom": "Doe",
    "prenom": "John",
    "type_utilisateur": "candidat"
  }'

# Connexion
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Chatbot (à implémenter)
```bash
curl -X POST http://localhost:8000/api/support/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Comment fonctionne le matching?",
    "language": "fr"
  }'
```

---

## 🎨 Nouvelles Fonctionnalités

### 🤖 Chatbot IA Multilingue

**Fichiers** :
- `website/js/ai-chatbot.js` - Logique
- `website/css/chatbot.css` - Styles

**Utilisation** :
1. Bouton flottant en bas à droite
2. Interface type messagerie
3. Suggestions contextuelles
4. Synchronisation avec changement de langue

**Personnalisation** :
```javascript
// Dans ai-chatbot.js
this.apiUrl = 'http://localhost:8000/api/support/chatbot';
```

### 🔒 Headers de Sécurité

**Automatiques sur toutes les réponses** :
- ✅ Protection XSS
- ✅ Protection clickjacking
- ✅ Force HTTPS
- ✅ CSP strict

**Configuration** :
```python
# Dans api/main.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        # ...
```

### ⏱️ Rate Limiting

**Protection contre abus** :
```python
# Exemple sur route de login
@router.post("/login")
@limiter.limit("5/minute")  # Max 5 tentatives/minute
async def login(request: Request, credentials: UserLogin):
    # ...
```

**Personnaliser** :
```python
# Global
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Par route
@limiter.limit("10/minute")
@limiter.limit("1000/day")
```

---

## 🔧 Configuration

### Variables d'environnement

**Fichier** : `.env`

```bash
# Application
APP_NAME=Recrut'der API
APP_VERSION=2.0.0
DEBUG=True

# Sécurité
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8001
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase
SUPABASE_URL=https://votre-url.supabase.co
SUPABASE_KEY=votre_anon_key
SUPABASE_SERVICE_KEY=votre_service_key

# JWT
JWT_SECRET=votre_secret_jwt
```

### CORS - Ajouter une origine

```python
# Dans api/config.py ou .env
CORS_ORIGINS=http://localhost:8001,http://localhost:3000,https://mon-domaine.com
```

### Rate Limiting - Ajuster les limites

```python
# Dans api/main.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"]
)
```

---

## 🐛 Dépannage

### Erreur : "No module named 'slowapi'"

```bash
source .venv/bin/activate
pip install slowapi
```

### Port 8000 déjà utilisé

```bash
# Trouver le processus
lsof -ti:8000

# Tuer le processus
lsof -ti:8000 | xargs kill
```

### Chatbot ne s'affiche pas

1. Vérifier que les fichiers sont chargés :
```html
<link rel="stylesheet" href="css/chatbot.css">
<script src="js/ai-chatbot.js"></script>
```

2. Ouvrir la console navigateur (F12) pour voir les erreurs

3. Vérifier que le serveur web sert bien les fichiers :
```bash
curl http://localhost:8001/js/ai-chatbot.js
```

### CORS error dans le navigateur

**Solution** : Ajouter l'origine dans `.env`
```bash
CORS_ORIGINS=http://localhost:8001,http://localhost:3000
```

Puis redémarrer l'API.

---

## 📚 Documentation Complète

### Fichiers de documentation

1. **`SECURITY_IMPROVEMENTS.md`** - Documentation sécurité complète
   - Headers HTTP détaillés
   - Rate limiting
   - CORS configuration
   - Guide production

2. **`RESUME_AMELIORATIONS.md`** - Résumé exécutif
   - Statistiques du projet
   - Checklist production
   - Prochaines étapes

3. **`README.md`** - Documentation projet générale

### Tests

```bash
# Tests de sécurité
python scripts/test_security.py

# Tests unitaires (si disponibles)
pytest

# Tests de charge (à créer)
locust -f tests/load_test.py
```

---

## 🎯 Checklist Développement

### Avant de coder

- [ ] `.venv` activé
- [ ] Variables `.env` configurées
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] API démarrée (`python run.py`)
- [ ] Site web accessible (`http://localhost:8001`)

### Avant de commit

- [ ] Code testé localement
- [ ] Pas d'erreurs dans la console
- [ ] Tests de sécurité passés (`python scripts/test_security.py`)
- [ ] Documentation mise à jour si nécessaire

### Avant déploiement

- [ ] `DEBUG=False` dans `.env`
- [ ] CORS configuré avec vrais domaines
- [ ] JWT_SECRET changé (256 bits aléatoires)
- [ ] SSL/TLS activé
- [ ] Tests de charge effectués
- [ ] Monitoring configuré

---

## 💡 Conseils Pratiques

### Développement

1. **Toujours tester en local** avant de pousser
2. **Utiliser des tokens différents** dev/prod
3. **Ne jamais commit** le fichier `.env`
4. **Tester sur plusieurs navigateurs**
5. **Vérifier la console** (F12) régulièrement

### Sécurité

1. **Changer JWT_SECRET** régulièrement (tous les 3 mois)
2. **Monitorer les logs** d'authentification
3. **Vérifier les headers** avec securityheaders.com
4. **Scanner vulnérabilités** avec OWASP ZAP
5. **Mettre à jour dépendances** mensuellement

### Performance

1. **Activer compression** GZip en production
2. **Utiliser CDN** pour assets statiques
3. **Optimiser images** (WebP, compression)
4. **Cache browser** configuré (max-age)
5. **Minimiser JS/CSS** en production

---

## 🚀 Prêt à Démarrer !

```bash
# Terminal 1 - API
source .venv/bin/activate
python run.py

# Terminal 2 - Website
cd website
python3 -m http.server 8001

# Terminal 3 - Tests
python scripts/test_security.py
```

Puis ouvrir :
- 📡 API : http://localhost:8000/docs
- 🌐 Site : http://localhost:8001/index.html
- 🤖 Chatbot : Cliquer sur le bouton en bas à droite

---

## 📞 Support

### Questions ?
- 📧 Email : support@recrutder.com
- 📚 Documentation : voir `SECURITY_IMPROVEMENTS.md`
- 🐛 Bugs : Ouvrir une issue GitHub

### Ressources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OWASP Security](https://owasp.org/)
- [Supabase Docs](https://supabase.com/docs)

---

**Bonne chance avec Recrut'der ! 🎉**
