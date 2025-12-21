# 🎯 Guide Workflow Intuitif avec IA

## Vue d'ensemble

Ce guide explique comment les candidats et recruteurs peuvent utiliser l'IA pour créer et peaufiner leurs profils/offres de manière **intuitive, précise et progressive**.

---

## 👤 Workflow Candidat - Création de Profil avec CV

### 📋 Étape 1 : Upload du CV

**Endpoint:** `POST /api/cv/upload-cv`

Le candidat upload son CV (PDF) :

```javascript
const formData = new FormData();
formData.append('file', cvFile);

const response = await fetch('/api/cv/upload-cv', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const result = await response.json();
// result.data : Données extraites du CV
// result.suggestions : Suggestions d'amélioration
```

**Résultat :**
```json
{
  "success": true,
  "data": {
    "informations_personnelles": {
      "nom": "Dupont",
      "prenom": "Jean",
      "email": "jean.dupont@email.com",
      "telephone": "0612345678",
      "ville": "Paris",
      "linkedin_url": "..."
    },
    "bio": "Développeur Full Stack avec 5 ans d'expérience...",
    "competences_techniques": ["JavaScript", "React", "Node.js", "Python"],
    "soft_skills": ["Communication", "Travail en équipe", "Autonomie"],
    "experience_totale_annees": 5,
    "formations": [...],
    "salaire_souhaite_min": 45000,
    "salaire_souhaite_max": 55000,
    ...
  },
  "suggestions": {
    "score_completude": 85,
    "points_forts": [
      "Profil technique solide",
      "Expérience variée"
    ],
    "suggestions_amelioration": [
      "Ajouter plus de détails sur les réalisations quantifiables",
      "Compléter les certifications"
    ],
    "bio_amelioree": "Version optimisée de la bio...",
    "competences_manquantes_suggere": ["Docker", "Kubernetes"]
  }
}
```

---

### ✏️ Étape 2 : Peaufinage Section par Section

Le candidat peut maintenant **modifier chaque section individuellement** sans tout re-sauvegarder.

#### Modifier les Compétences

**Endpoint:** `PATCH /api/cv/update-profile-section`

```javascript
await fetch('/api/cv/update-profile-section', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    competences_techniques: ["JavaScript", "React", "Node.js", "Python", "Docker"]
    // Ajout de Docker après suggestion
  })
});
```

#### Modifier le Salaire

```javascript
await fetch('/api/cv/update-profile-section', {
  method: 'PATCH',
  body: JSON.stringify({
    salaire_min: 50000,  // Ajustement
    salaire_max: 60000
  })
});
```

#### Modifier l'Expérience

```javascript
await fetch('/api/cv/update-profile-section', {
  method: 'PATCH',
  body: JSON.stringify({
    experience_annees: 6  // Correction
  })
});
```

**Avantage :** Chaque modification met automatiquement à jour le **score de complétude** du profil.

---

### 💡 Étape 3 : Demander des Suggestions IA par Section

Le candidat peut demander à l'IA d'améliorer une section spécifique.

**Endpoint:** `POST /api/cv/improve-section`

#### Améliorer la Bio

```javascript
const response = await fetch('/api/cv/improve-section', {
  method: 'POST',
  body: JSON.stringify({
    section_name: "bio",
    section_data: {
      bio: "Développeur Full Stack avec 5 ans d'expérience..."
    }
  })
});

const result = await response.json();
```

**Réponse :**
```json
{
  "success": true,
  "section": "bio",
  "suggestions": {
    "score_actuel": 70,
    "points_forts": [
      "Mentionne l'expérience",
      "Clair et concis"
    ],
    "suggestions": [
      "Ajouter vos réalisations clés",
      "Mentionner les technologies maîtrisées",
      "Quantifier votre impact"
    ],
    "version_amelioree": "Développeur Full Stack passionné avec 5 ans d'expérience en JavaScript/React/Node.js. J'ai contribué au développement de 10+ applications web scalables, optimisant les performances de 40% en moyenne. Expert en architecture microservices et déploiement CI/CD.",
    "exemples": [
      "Spécialisé en [technologie] avec [X] années d'expérience",
      "Passionné par [domaine], j'ai réalisé [réalisation quantifiée]"
    ],
    "mots_cles_manquants": ["scalable", "performance", "architecture"]
  }
}
```

#### Améliorer les Compétences

```javascript
await fetch('/api/cv/improve-section', {
  method: 'POST',
  body: JSON.stringify({
    section_name: "competences",
    section_data: {
      competences_techniques: ["JavaScript", "React", "Node.js"],
      secteurs: ["tech", "startup"]
    }
  })
});
```

**L'IA suggère :**
- Compétences manquantes populaires dans le secteur
- Organisation des compétences par catégorie
- Niveau de maîtrise recommandé

---

### 📊 Étape 4 : Suivi de la Complétude

**Endpoint:** `GET /api/cv/profile-completeness`

```javascript
const response = await fetch('/api/cv/profile-completeness');
const result = await response.json();
```

**Réponse :**
```json
{
  "completude": 90,
  "sections_manquantes": [
    "Langues"  // Seule section manquante
  ],
  "actif": true
}
```

**Interface recommandée :**
```
┌────────────────────────────────────────┐
│  Complétude de votre profil: 90% ✅   │
│  ████████████████████░░                │
│                                        │
│  Sections complètes:                   │
│  ✅ Compétences techniques            │
│  ✅ Soft skills                        │
│  ✅ Expérience                         │
│  ✅ Qualifications                     │
│  ✅ Salaire souhaité                   │
│  ✅ Localisation                       │
│  ✅ Secteurs                           │
│                                        │
│  Sections à compléter:                 │
│  ⚠️  Langues → [Ajouter]               │
└────────────────────────────────────────┘
```

---

### ✅ Étape 5 : Validation Finale

**Endpoint:** `POST /api/cv/validate-and-save`

Quand tout est validé, sauvegarder définitivement :

```javascript
await fetch('/api/cv/validate-and-save', {
  method: 'POST',
  body: JSON.stringify(cv_data)  // Données finales complètes
});
```

**Le profil passe à `actif: true`** et est visible par les recruteurs.

---

## 🏢 Workflow Recruteur - Création d'Offre

### 📋 Étape 1 : Upload de la Fiche de Poste

**Endpoint:** `POST /api/job/upload-job-description`

Le recruteur upload sa fiche de poste (PDF, DOCX ou texte) :

```javascript
const formData = new FormData();
formData.append('file', ficheFile);
formData.append('auto_detect_language', true);
formData.append('target_language', 'fr');

const response = await fetch('/api/job/upload-job-description', {
  method: 'POST',
  body: formData
});
```

**Résultat :**
```json
{
  "success": true,
  "langue_detectee": "en",
  "langue_sortie": "fr",
  "data": {
    "titre_poste": "Développeur Full Stack Senior",
    "entreprise": "TechStartup",
    "description_complete": "...",
    "description_courte": "Rejoignez notre équipe...",
    "competences_requises": ["JavaScript", "React", "Node.js"],
    "competences_bonus": ["Docker", "Kubernetes"],
    "soft_skills_recherches": ["Communication", "Autonomie"],
    "experience_min": 5,
    "experience_max": 8,
    "salaire_min": 55000,
    "salaire_max": 70000,
    "localisation": "Paris",
    "ville": "Paris",
    "remote_possible": true,
    "politique_teletravail": "hybride",
    "avantages": ["Tickets restaurant", "Mutuelle", "RTT"],
    ...
  }
}
```

---

### ✏️ Étape 2 : Modification Section par Section

**Endpoint:** `PATCH /api/job/update-offer-section/{offre_id}`

#### Ajuster le Salaire

```javascript
await fetch(`/api/job/update-offer-section/${offreId}`, {
  method: 'PATCH',
  body: JSON.stringify({
    salaire_min: 60000,  // Augmentation
    salaire_max: 75000
  })
});
```

#### Ajouter des Avantages

```javascript
await fetch(`/api/job/update-offer-section/${offreId}`, {
  method: 'PATCH',
  body: JSON.stringify({
    avantages: [
      "Tickets restaurant",
      "Mutuelle premium",
      "RTT",
      "Budget formation 2000€",  // Ajout
      "MacBook Pro"               // Ajout
    ]
  })
});
```

#### Modifier le Titre

```javascript
await fetch(`/api/job/update-offer-section/${offreId}`, {
  method: 'PATCH',
  body: JSON.stringify({
    titre: "Lead Developer Full Stack (Remote)"  // Plus attractif
  })
});
```

---

### 💡 Étape 3 : Suggestions IA par Section

**Endpoint:** `POST /api/job/improve-offer-section/{offre_id}`

#### Améliorer la Description

```javascript
const response = await fetch(`/api/job/improve-offer-section/${offreId}`, {
  method: 'POST',
  body: JSON.stringify({
    section_name: "description",
    section_data: {
      description: "Nous recherchons un développeur..."
    }
  })
});
```

**Réponse :**
```json
{
  "success": true,
  "suggestions": {
    "score_actuel": 65,
    "points_forts": [
      "Objectifs clairs",
      "Responsabilités définies"
    ],
    "suggestions": [
      "Ajouter des informations sur la culture d'entreprise",
      "Mentionner les technologies utilisées",
      "Préciser l'impact du poste",
      "Ajouter des détails sur l'équipe"
    ],
    "version_amelioree": "Rejoignez notre équipe de 20 développeurs passionnés ! Nous construisons une plateforme SaaS innovante utilisée par 10 000+ entreprises. En tant que Lead Developer, vous aurez un impact direct sur l'architecture de nos microservices (Node.js/React) et mentorerez 3 développeurs juniors. Stack technique moderne : TypeScript, React, GraphQL, Kubernetes, AWS. Culture agile, code reviews quotidiennes, déploiements continus.",
    "mots_cles_manquants": ["équipe", "impact", "stack technique", "culture"],
    "conseil_attractivite": "Mettez en avant les défis techniques intéressants et l'opportunité de croissance"
  }
}
```

#### Améliorer les Compétences

```javascript
await fetch(`/api/job/improve-offer-section/${offreId}`, {
  method: 'POST',
  body: JSON.stringify({
    section_name: "competences",
    section_data: {
      competences_requises: ["JavaScript", "React"],
      secteur: "tech"
    }
  })
});
```

**L'IA suggère :**
- Compétences techniques manquantes importantes
- Équilibre entre must-have et nice-to-have
- Compétences trop restrictives à assouplir

---

### 📊 Étape 4 : Vérifier la Complétude

**Endpoint:** `GET /api/job/offer-completeness/{offre_id}`

```javascript
const response = await fetch(`/api/job/offer-completeness/${offreId}`);
```

**Réponse :**
```json
{
  "offre_id": "123",
  "completude_obligatoire": 100,
  "score_qualite_global": 85,
  "sections_manquantes": [],
  "sections_optionnelles_manquantes": [
    "Compétences bonus",
    "Missions principales"
  ],
  "statut": "brouillon",
  "pret_publication": true
}
```

**Interface recommandée :**
```
┌────────────────────────────────────────┐
│  Qualité de votre offre: 85% 🟡       │
│  ████████████████████░░░░              │
│                                        │
│  Champs obligatoires: 100% ✅         │
│  ✅ Titre                              │
│  ✅ Description                        │
│  ✅ Compétences requises               │
│  ✅ Expérience minimale                │
│  ✅ Salaire                            │
│  ✅ Localisation                       │
│  ✅ Type de contrat                    │
│                                        │
│  Recommandations (optionnel):          │
│  💡 Compétences bonus → [Ajouter]     │
│  💡 Missions principales → [Ajouter]  │
│                                        │
│  [📝 Améliorer avec l'IA]              │
│  [✅ Publier l'offre]                  │
└────────────────────────────────────────┘
```

---

### 🌍 Étape 5 (Optionnelle) : Traduction

**Endpoint:** `POST /api/job/translate-job-description`

Traduire l'offre pour toucher un public international :

```javascript
await fetch('/api/job/translate-job-description', {
  method: 'POST',
  body: JSON.stringify({
    job_data: offreData,
    target_language: "en"  // Anglais
  })
});
```

Publiez la même offre en **10 langues** différentes !

---

### ✅ Étape 6 : Publication

**Endpoint:** `POST /api/job/validate-and-create-offer`

```javascript
await fetch('/api/job/validate-and-create-offer', {
  method: 'POST',
  body: JSON.stringify({ job_data: finalData })
});
```

**L'offre passe à `statut: "publiee"`** et est visible par les candidats.

---

## 🎨 Recommandations UI/UX

### Pour les Candidats

#### Écran de Parsing CV
```
┌─────────────────────────────────────────┐
│  ✅ CV analysé avec succès !            │
│  Score de complétude: 85%               │
├─────────────────────────────────────────┤
│                                         │
│  [Onglets]                              │
│  📋 Infos  💼 Expérience  🎓 Formation  │
│                                         │
│  👤 Informations Personnelles           │
│  Nom: [Jean Dupont]          ✏️         │
│  Email: [jean@email.com]     ✏️         │
│  Téléphone: [0612345678]     ✏️         │
│  Ville: [Paris]              ✏️         │
│                                         │
│  💡 Suggestion IA:                      │
│  "Ajoutez votre portfolio pour +15%    │
│   de visibilité"                        │
│   [Ajouter] [Ignorer]                   │
│                                         │
│  💼 Compétences Techniques              │
│  JavaScript ✅  React ✅  Node.js ✅    │
│  [+ Ajouter une compétence]             │
│                                         │
│  💡 L'IA suggère: Docker, Kubernetes    │
│  [Ajouter Docker] [Ajouter Kubernetes]  │
│                                         │
│  [⬅️ Précédent]  [Suivant ➡️]           │
│  [💾 Sauvegarder]  [✅ Valider]         │
└─────────────────────────────────────────┘
```

#### Boutons d'Action sur Chaque Section
```
┌─────────────────────────────────┐
│  💼 Compétences Techniques      │
│                                 │
│  JavaScript, React, Node.js     │
│                                 │
│  [✏️ Modifier]  [💡 Améliorer]  │
└─────────────────────────────────┘
```

### Pour les Recruteurs

#### Écran de Parsing d'Offre
```
┌─────────────────────────────────────────┐
│  ✅ Fiche de poste analysée !           │
│  Langue: Anglais → Français             │
│  Qualité: 75% 🟡                        │
├─────────────────────────────────────────┤
│                                         │
│  [Onglets]                              │
│  📋 Infos  💰 Rémunération  🎯 Profil   │
│                                         │
│  📋 Informations Générales              │
│  Titre: [Développeur Full Stack...]    │
│  [✏️ Modifier]  [💡 Améliorer le titre] │
│                                         │
│  Description courte:                    │
│  [Rejoignez notre équipe...]            │
│  [✏️ Modifier]  [💡 Optimiser]          │
│                                         │
│  💡 Suggestions IA:                     │
│  • Ajouter la culture d'entreprise      │
│  • Préciser les opportunités d'évolution│
│  • Mentionner les projets techniques    │
│                                         │
│  🎯 Profil Recherché                    │
│  Compétences requises:                  │
│  JavaScript ✅  React ✅  Node.js ✅    │
│  [+ Ajouter]  [💡 Suggestions IA]       │
│                                         │
│  💡 L'IA suggère d'ajouter: TypeScript  │
│  [Ajouter en must-have]                 │
│  [Ajouter en nice-to-have]              │
│                                         │
│  [💾 Sauvegarder brouillon]             │
│  [🌍 Traduire en...]                    │
│  [✅ Publier l'offre]                   │
└─────────────────────────────────────────┘
```

---

## 🔄 Flux Complet Résumé

### Candidat
```
1. Upload CV PDF
   ↓
2. IA parse et extrait tout
   ↓
3. Affichage section par section
   ↓
4. Candidat modifie/corrige chaque section
   ↓
5. Demande suggestions IA sur sections spécifiques
   ↓
6. Applique les améliorations
   ↓
7. Vérifie la complétude (90%+)
   ↓
8. Validation finale → Profil actif ✅
```

### Recruteur
```
1. Upload fiche de poste (PDF/DOCX/Texte)
   ↓
2. IA parse et traduit si nécessaire
   ↓
3. Affichage section par section
   ↓
4. Recruteur modifie/corrige/enrichit
   ↓
5. Demande suggestions IA sur sections
   ↓
6. Améliore titre, description, avantages
   ↓
7. Vérifie la qualité (85%+)
   ↓
8. (Optionnel) Traduit en d'autres langues
   ↓
9. Publication → Offre publiée ✅
```

---

## 💡 Conseils d'Implémentation

### 1. Sauvegarde Automatique
- Sauvegarder automatiquement chaque modification
- Pas de perte de données si le navigateur se ferme
- Status "brouillon" jusqu'à validation finale

### 2. Feedback Visuel
- Indicateur de complétude en temps réel
- Badges ✅ sur sections complètes
- Alertes ⚠️ sur sections incomplètes
- Animation lors de l'amélioration du score

### 3. Guidage Progressif
- Afficher une section à la fois (wizard)
- Bouton "Suivant" grisé si section invalide
- Tooltips explicatifs sur chaque champ
- Exemples pré-remplis au survol

### 4. Suggestions Contextuelles
- Bulle de suggestion à côté de chaque champ
- "💡 Astuce IA" toujours visible
- Possibilité d'appliquer en 1 clic
- Historique des suggestions refusées

### 5. Validation Intelligente
- Validation en temps réel (pas uniquement à la soumission)
- Messages d'erreur clairs et constructifs
- Suggestions de correction automatiques
- Limites min/max affichées

---

## 📊 Métriques de Succès

- **Temps moyen de création de profil** : < 5 minutes (vs 20 min manuel)
- **Taux de complétude** : > 90%
- **Taux d'utilisation des suggestions IA** : > 60%
- **Score qualité moyen** : > 85%
- **Taux d'abandon** : < 10%

---

## 🚀 Prochaines Étapes

1. ✅ Backend créé et testé
2. ⏳ Intégration frontend (en cours)
3. ⏳ Tests utilisateurs
4. ⏳ Optimisation UX basée sur feedback
5. ⏳ A/B testing des suggestions IA

---

**Développé avec ❤️ par GitHub Copilot**  
Date: 21 décembre 2025
