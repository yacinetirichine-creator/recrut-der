# 🤖 PHASE 3 : ESPACE CANDIDAT & IA CV - Guide d'Installation

## ✅ Ce qui a été créé

### 1. **Service IA de Parsing CV** (`api/services/cv_parser_service.py`)
- Extraction automatique de texte depuis PDF
- Parsing intelligent avec OpenAI GPT-4 ou Claude
- Génération de suggestions d'amélioration
- Analyse de match CV/offre avec IA

### 2. **Routes API CV** (`api/routes/cv_ai.py`)
- `POST /api/cv/upload-cv` - Upload et parse un CV PDF
- `POST /api/cv/parse-text` - Parse du texte brut
- `POST /api/cv/validate-and-save` - Sauvegarder les données validées
- `POST /api/cv/match-with-job/{offre_id}` - Analyser le match avec une offre
- `GET /api/cv/profile-completeness` - % de complétude du profil

---

## 🔧 INSTALLATION - Vos Actions

### **Étape 1 : Installer les nouvelles dépendances**

```bash
# Installer OpenAI, Anthropic et PyPDF2
pip install openai==1.54.0 anthropic==0.39.0 PyPDF2==3.0.1
```

### **Étape 2 : Choisir votre IA**

Vous devez choisir **OpenAI** ou **Claude (Anthropic)** :

#### Option A : OpenAI (Recommandé - Plus économique)

1. Créer un compte sur https://platform.openai.com
2. Aller dans https://platform.openai.com/api-keys
3. Créer une nouvelle clé API
4. Copier la clé (commence par `sk-...`)

#### Option B : Anthropic Claude

1. Créer un compte sur https://console.anthropic.com
2. Aller dans API Keys
3. Créer une nouvelle clé
4. Copier la clé (commence par `sk-ant-...`)

### **Étape 3 : Ajouter la clé dans .env**

Ouvrez votre fichier `.env` et ajoutez :

```env
# IA - Clés API (choisir OpenAI OU Anthropic)
OPENAI_API_KEY=sk-votre_vraie_cle_ici
# OU
# ANTHROPIC_API_KEY=sk-ant-votre_vraie_cle_ici
```

⚠️ **IMPORTANT** : Remplacez `sk-votre_vraie_cle_ici` par votre VRAIE clé API !

### **Étape 4 : Relancer le serveur**

```bash
# Arrêter le serveur actuel (Ctrl+C)
# Puis relancer
python run.py
```

---

## 🎯 TESTER LES FONCTIONNALITÉS

### Test 1 : Upload d'un CV PDF

Allez sur http://localhost:8000/docs

1. Cliquez sur `POST /api/cv/upload-cv`
2. Cliquez sur "Try it out"
3. Uploadez un fichier PDF de CV
4. Exécutez
5. L'IA va extraire et structurer toutes les infos !

### Test 2 : Vérifier la complétude du profil

1. `GET /api/cv/profile-completeness`
2. Voir le pourcentage et les sections manquantes

### Test 3 : Analyser un match avec une offre

1. `POST /api/cv/match-with-job/{offre_id}`
2. Obtenir un score de match et des explications

---

## 📊 WORKFLOW CANDIDAT

```
1. CANDIDAT UPLOAD SON CV (PDF)
   ↓
2. IA EXTRAIT LE TEXTE
   ↓
3. IA PARSE ET STRUCTURE LES DONNÉES
   - Infos personnelles
   - Expériences
   - Formations
   - Compétences
   - Langues
   - etc.
   ↓
4. IA GÉNÈRE DES SUGGESTIONS
   - Score de complétude
   - Points forts
   - Améliorations possibles
   - Bio optimisée
   ↓
5. CANDIDAT VALIDE/MODIFIE ÉTAPE PAR ÉTAPE
   ↓
6. SAUVEGARDE DANS LE PROFIL
   ↓
7. PROFIL ACTIF → VISIBLE PAR LES RECRUTEURS
```

---

## 💰 COÛT ESTIMÉ

### OpenAI GPT-4o-mini
- **Parsing d'un CV** : ~$0.01 - $0.02 (1-2 centimes)
- **Suggestions** : ~$0.005 (0.5 centime)
- **Match avec offre** : ~$0.01 (1 centime)

**Total par candidat** : ~3-4 centimes d'euros

### Anthropic Claude 3.5 Sonnet
- **Parsing d'un CV** : ~$0.03 - $0.05
- **Suggestions** : ~$0.01
- **Match avec offre** : ~$0.02

**Total par candidat** : ~6-8 centimes d'euros

💡 **Recommandation** : Utiliser OpenAI GPT-4o-mini (moins cher et très performant)

---

## 🚨 DÉPANNAGE

### Erreur "Service d'IA non configuré"
→ Vous n'avez pas ajouté la clé API dans `.env`

### Erreur "Invalid API key"
→ Vérifiez que vous avez copié la clé complète

### Erreur "pip install openai"
→ Activez votre environnement virtuel : `source .venv/bin/activate`

### Le parsing ne fonctionne pas bien
→ Essayez avec un autre modèle ou vérifiez la qualité du PDF

---

## ✅ CONFIRMEZ POUR CONTINUER

**Dites-moi quand vous avez :**
1. ✅ Installé les dépendances (`pip install ...`)
2. ✅ Créé votre clé API OpenAI ou Anthropic
3. ✅ Ajouté la clé dans `.env`
4. ✅ Relancé le serveur

**Ensuite on passe à la Phase 4 : Matching IA type Tinder !** 🚀
