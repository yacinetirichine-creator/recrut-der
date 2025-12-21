# ╔═══════════════════════════════════════════════════════════════╗
# ║  RECRUT'DER - Guide de Configuration Supabase                ║
# ╚═══════════════════════════════════════════════════════════════╝

## 🚀 Configuration Supabase en 5 étapes

### **Étape 1 : Créer le schéma de base de données**

1. Allez sur https://app.supabase.com/project/tlczregxeuyybtzsqdsj/editor
2. Cliquez sur "SQL Editor" dans le menu de gauche
3. Créez une nouvelle query
4. Copiez TOUT le contenu du fichier `supabase/schema.sql`
5. Exécutez la query (bouton RUN ou Ctrl+Enter)

✅ Cela va créer toutes les tables, relations, index et politiques de sécurité.

---

### **Étape 2 : Récupérer vos clés API**

1. Allez sur https://app.supabase.com/project/tlczregxeuyybtzsqdsj/settings/api
2. Copiez ces valeurs :
   - **Project URL** (déjà connue): `https://tlczregxeuyybtzsqdsj.supabase.co`
   - **anon public** (clé publique)
   - **service_role** (clé secrète - ADMIN)

---

### **Étape 3 : Récupérer votre JWT Secret**

1. Allez sur https://app.supabase.com/project/tlczregxeuyybtzsqdsj/settings/api
2. Faites défiler jusqu'à **"JWT Settings"**
3. Copiez le **JWT Secret**

---

### **Étape 4 : Créer votre fichier .env**

1. À la racine du projet, créez un fichier `.env` (PAS `.env.example`)
2. Remplissez-le avec vos vraies valeurs :

```env
# Application
APP_NAME=Recrut'der API
APP_VERSION=2.0.0
DEBUG=True

# Serveur
HOST=0.0.0.0
PORT=8000

# Supabase Configuration
SUPABASE_URL=https://tlczregxeuyybtzsqdsj.supabase.co
SUPABASE_KEY=votre_anon_key_ici
SUPABASE_SERVICE_KEY=votre_service_role_key_ici

# JWT Secret
JWT_SECRET=votre_jwt_secret_ici
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
```

---

### **Étape 5 : Installer et lancer**

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt

# Lancer l'API
python run.py
```

---

## 📡 Tester l'API

### **1. Créer un compte candidat**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidat@example.com",
    "password": "password123",
    "nom": "Dupont",
    "prenom": "Jean",
    "type_utilisateur": "candidat"
  }'
```

### **2. Créer un compte recruteur**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruteur@example.com",
    "password": "password123",
    "nom": "Martin",
    "prenom": "Sophie",
    "type_utilisateur": "recruteur",
    "entreprise": "TechCorp",
    "poste": "DRH"
  }'
```

### **3. Se connecter**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidat@example.com",
    "password": "password123"
  }'
```

Vous recevrez un **token** à utiliser pour les requêtes authentifiées :

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "candidat@example.com",
    "type_utilisateur": "candidat"
  }
}
```

### **4. Accéder à son profil**

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI"
```

---

## 🎯 Architecture de la base de données

### **Tables créées**

1. **utilisateurs** - Profils communs (candidats + recruteurs)
2. **candidats** - Profils détaillés des candidats
3. **recruteurs** - Profils détaillés des recruteurs
4. **offres** - Offres d'emploi publiées
5. **matchings** - Résultats de matching IA sauvegardés
6. **candidatures** - Candidatures envoyées

### **Sécurité (Row Level Security)**

✅ Les candidats voient uniquement leurs données  
✅ Les recruteurs voient uniquement leurs offres  
✅ Les offres publiées sont visibles par tous  
✅ Les matchings sont visibles uniquement par les parties concernées

---

## 📚 Documentation API

Une fois l'API lancée, accédez à :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## 🔒 Sécurité

⚠️ **IMPORTANT** : Ne committez JAMAIS le fichier `.env` sur Git !

Le fichier `.gitignore` est configuré pour l'exclure automatiquement.

---

## 📝 Prochaines étapes recommandées

1. ✅ Tester l'inscription et la connexion
2. ✅ Compléter un profil candidat via l'API
3. ✅ Créer une offre en tant que recruteur
4. ✅ Tester le matching IA entre candidats et offres
5. 🔜 Développer un frontend (React/Vue/Svelte)
6. 🔜 Ajouter des photos de profil (Supabase Storage)
7. 🔜 Ajouter des notifications (emails/push)

---

## 🆘 Problèmes courants

### **Erreur : "SUPABASE_URL not found"**
➡️ Vérifiez que le fichier `.env` existe et contient les bonnes valeurs

### **Erreur : "relation does not exist"**
➡️ Exécutez le fichier `supabase/schema.sql` dans l'éditeur SQL de Supabase

### **Erreur : "JWT malformed"**
➡️ Vérifiez que `JWT_SECRET` correspond bien à celui de Supabase

---

## 📧 Support

Pour toute question, contactez l'équipe de développement.
