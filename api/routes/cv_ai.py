"""
📄 Recrut'der - Routes IA pour CV
==================================
Upload, parsing automatique et suggestions IA pour les CV
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Dict, Any
from uuid import UUID

from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from api.services.cv_parser_service import CVParserService
from api.config import settings
from loguru import logger


router = APIRouter()

# Initialiser le service CV Parser (à configurer avec votre clé API)
# Pour l'instant, on le laisse optionnel
cv_parser = None

def get_cv_parser() -> CVParserService:
    """Obtenir le service de parsing CV"""
    global cv_parser
    
    if cv_parser is None:
        # Vérifier si une clé API IA est configurée
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        
        if openai_key:
            cv_parser = CVParserService(api_key=openai_key, provider="openai")
            logger.info("✅ Service CV Parser initialisé avec OpenAI")
        elif anthropic_key:
            cv_parser = CVParserService(api_key=anthropic_key, provider="anthropic")
            logger.info("✅ Service CV Parser initialisé avec Claude")
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service d'IA non configuré. Ajoutez OPENAI_API_KEY ou ANTHROPIC_API_KEY dans .env"
            )
    
    return cv_parser


@router.post("/upload-cv")
async def upload_and_parse_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    📤 Upload et parsing automatique d'un CV (PDF)
    
    1. Upload le fichier PDF
    2. Extrait le texte
    3. Parse avec l'IA
    4. Retourne les données structurées
    
    Le candidat pourra ensuite valider/modifier chaque section
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les candidats peuvent uploader un CV"
            )
        
        # Vérifier le type de fichier
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seuls les fichiers PDF sont acceptés"
            )
        
        # Obtenir le service de parsing
        parser = get_cv_parser()
        
        # Extraire le texte du PDF
        logger.info(f"📄 Extraction du texte de {file.filename}...")
        cv_text = await parser.extract_text_from_pdf(file)
        
        # Parser le CV avec l'IA
        logger.info("🤖 Parsing du CV avec l'IA...")
        cv_data = await parser.parse_cv_from_text(cv_text)
        
        # Générer des suggestions d'amélioration
        logger.info("💡 Génération des suggestions...")
        suggestions = await parser.generate_profile_suggestions(cv_data)
        
        logger.info(f"✅ CV parsé avec succès pour {current_user['email']}")
        
        return {
            "success": True,
            "message": "CV analysé avec succès",
            "data": cv_data,
            "suggestions": suggestions,
            "candidat_id": candidat.data["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur upload CV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement du CV: {str(e)}"
        )


@router.post("/parse-text")
async def parse_cv_from_text(
    cv_text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    🤖 Parser un CV à partir de texte brut
    
    Utile si le candidat colle directement son CV en texte
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les candidats peuvent parser un CV"
            )
        
        # Obtenir le service de parsing
        parser = get_cv_parser()
        
        # Parser le CV
        cv_data = await parser.parse_cv_from_text(cv_text)
        
        # Générer des suggestions
        suggestions = await parser.generate_profile_suggestions(cv_data)
        
        return {
            "success": True,
            "data": cv_data,
            "suggestions": suggestions,
            "candidat_id": candidat.data["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur parsing texte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate-and-save")
async def validate_and_save_cv_data(
    cv_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Valider et sauvegarder les données du CV parsé
    
    Après que le candidat a validé/modifié les informations extraites,
    on met à jour son profil dans la base de données
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les candidats peuvent sauvegarder un CV"
            )
        
        candidat_id = candidat.data["id"]
        
        # Extraire les données pertinentes pour le profil candidat
        info_perso = cv_data.get("informations_personnelles", {})
        
        # Mettre à jour le profil candidat
        update_data = {
            "competences_techniques": cv_data.get("competences_techniques", []),
            "soft_skills": cv_data.get("soft_skills", []),
            "experience_annees": cv_data.get("experience_totale_annees", 0),
            "qualifications": [f["diplome"] for f in cv_data.get("formations", [])],
            "niveau_etudes": cv_data.get("formations", [{}])[0].get("niveau", "bac+3") if cv_data.get("formations") else "bac+3",
            "salaire_min": cv_data.get("salaire_souhaite_min", 0),
            "salaire_max": cv_data.get("salaire_souhaite_max", 0),
            "localisation": info_perso.get("ville", "Non spécifié"),
            "disponibilite": cv_data.get("disponibilite", "1_mois"),
            "secteurs": cv_data.get("secteurs_cibles", []),
            "type_contrat_souhaite": cv_data.get("type_contrat_souhaite", ["cdi"]),
            "langues": [l["langue"] for l in cv_data.get("langues", [])],
            "taille_entreprise_preferee": cv_data.get("taille_entreprise_preferee", []),
            "actif": True  # Profil activé une fois complété
        }
        
        result = supabase.table("candidats")\
            .update(update_data)\
            .eq("id", candidat_id)\
            .execute()
        
        # Mettre à jour les infos utilisateur
        user_update = {
            "nom": info_perso.get("nom", current_user.get("nom")),
            "prenom": info_perso.get("prenom", current_user.get("prenom")),
            "telephone": info_perso.get("telephone"),
            "bio": cv_data.get("bio"),
            "linkedin_url": info_perso.get("linkedin_url"),
        }
        
        supabase.table("utilisateurs")\
            .update(user_update)\
            .eq("id", current_user["id"])\
            .execute()
        
        logger.info(f"✅ Profil candidat mis à jour: {candidat_id}")
        
        return {
            "success": True,
            "message": "Profil mis à jour avec succès",
            "candidat_id": candidat_id,
            "completude": 100
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde CV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/match-with-job/{offre_id}")
async def match_cv_with_job(
    offre_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Analyser le match entre le CV du candidat et une offre d'emploi
    
    Retourne un score et des explications détaillées
    """
    try:
        # Récupérer le candidat
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Profil candidat non trouvé"
            )
        
        # Récupérer l'offre
        offre = supabase.table("offres")\
            .select("*")\
            .eq("id", str(offre_id))\
            .single()\
            .execute()
        
        if not offre.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre non trouvée"
            )
        
        # Construire le profil candidat pour l'IA
        cv_data = {
            "competences_techniques": candidat.data.get("competences_techniques", []),
            "soft_skills": candidat.data.get("soft_skills", []),
            "experience_annees": candidat.data.get("experience_annees", 0),
            "qualifications": candidat.data.get("qualifications", []),
            "secteurs": candidat.data.get("secteurs", []),
        }
        
        # Construire la description de l'offre
        job_description = f"""
Titre: {offre.data['titre']}
Entreprise: {offre.data['entreprise']}
Description: {offre.data.get('description', '')}
Compétences requises: {', '.join(offre.data.get('competences_requises', []))}
Compétences bonus: {', '.join(offre.data.get('competences_bonus', []))}
Expérience minimale: {offre.data.get('experience_min', 0)} ans
Salaire: {offre.data.get('salaire_min', 0)} - {offre.data.get('salaire_max', 0)} €
Localisation: {offre.data.get('localisation', '')}
Type de contrat: {offre.data.get('type_contrat', '')}
"""
        
        # Obtenir le service de parsing
        parser = get_cv_parser()
        
        # Analyser le match
        match_analysis = await parser.match_with_job_description(cv_data, job_description)
        
        return {
            "success": True,
            "offre_id": str(offre_id),
            "candidat_id": candidat.data["id"],
            "analysis": match_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur analyse match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/profile-completeness")
async def get_profile_completeness(current_user: dict = Depends(get_current_user)):
    """
    📊 Calculer le % de complétude du profil candidat
    """
    try:
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            return {"completude": 0, "sections_manquantes": ["Tout"]}
        
        data = candidat.data
        total_fields = 0
        completed_fields = 0
        sections_manquantes = []
        
        # Vérifier chaque section
        checks = {
            "Compétences techniques": len(data.get("competences_techniques", [])) > 0,
            "Soft skills": len(data.get("soft_skills", [])) > 0,
            "Expérience": data.get("experience_annees", 0) > 0,
            "Qualifications": len(data.get("qualifications", [])) > 0,
            "Salaire souhaité": data.get("salaire_min", 0) > 0 and data.get("salaire_max", 0) > 0,
            "Localisation": data.get("localisation") and data.get("localisation") != "à définir",
            "Secteurs": len(data.get("secteurs", [])) > 0,
            "Langues": len(data.get("langues", [])) > 0,
        }
        
        for section, is_complete in checks.items():
            total_fields += 1
            if is_complete:
                completed_fields += 1
            else:
                sections_manquantes.append(section)
        
        completude = int((completed_fields / total_fields) * 100)
        
        return {
            "completude": completude,
            "sections_manquantes": sections_manquantes,
            "actif": data.get("actif", False)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul complétude: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/update-profile-section")
async def update_profile_section(
    section_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    ✏️ Mise à jour partielle du profil candidat (section par section)
    
    Permet au candidat de modifier une section spécifique sans tout re-sauvegarder.
    Parfait pour peaufiner le profil après le parsing IA.
    
    Exemples de sections:
    - competences_techniques: ["Python", "React", ...]
    - soft_skills: ["Communication", ...]
    - experience_annees: 5
    - salaire_min: 45000
    - localisation: "Paris"
    - etc.
    """
    try:
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil candidat non trouvé"
            )
        
        # Valider que les champs existent
        allowed_fields = [
            "competences_techniques", "soft_skills", "experience_annees",
            "qualifications", "niveau_etudes", "salaire_min", "salaire_max",
            "localisation", "accept_remote", "preference_teletravail",
            "secteurs", "type_contrat_souhaite", "disponibilite",
            "langues", "taille_entreprise_preferee", "cv_url", "portfolio_url"
        ]
        
        update_data = {}
        for field, value in section_data.items():
            if field in allowed_fields:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun champ valide à mettre à jour"
            )
        
        # Mettre à jour
        result = supabase.table("candidats")\
            .update(update_data)\
            .eq("user_id", current_user["id"])\
            .execute()
        
        # Recalculer la complétude
        updated = await get_profile_completeness(current_user)
        
        logger.info(f"✅ Profil mis à jour: {list(update_data.keys())}")
        
        return {
            "success": True,
            "message": f"{len(update_data)} champ(s) mis à jour",
            "updated_fields": list(update_data.keys()),
            "completude": updated.get("completude", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour section: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/improve-section")
async def improve_profile_section(
    section_name: str,
    section_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    💡 Obtenir des suggestions IA pour améliorer une section spécifique
    
    Le candidat peut demander des conseils pour améliorer:
    - Sa bio
    - Ses compétences
    - La description de son expérience
    - Ses soft skills
    - etc.
    
    Args:
        section_name: Nom de la section (bio, competences, experience, etc.)
        section_data: Données actuelles de la section
    """
    try:
        candidat = supabase.table("candidats")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not candidat.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil candidat non trouvé"
            )
        
        parser = get_cv_parser()
        
        # Construire un prompt personnalisé selon la section
        prompt = f"""
Analyse cette section du profil candidat et donne des suggestions d'amélioration.

SECTION: {section_name}
DONNÉES ACTUELLES:
{section_data}

PROFIL COMPLET:
- Compétences: {candidat.data.get('competences_techniques', [])}
- Expérience: {candidat.data.get('experience_annees', 0)} ans
- Secteurs: {candidat.data.get('secteurs', [])}

RETOURNE un JSON avec:
{{
    "score_actuel": 75,
    "points_forts": ["...", "..."],
    "suggestions": ["...", "..."],
    "version_amelioree": "Version améliorée de la section",
    "exemples": ["Exemple 1", "Exemple 2"],
    "mots_cles_manquants": ["mot-clé 1", "..."]
}}

Sois précis, constructif et actionnable.
"""
        
        if parser.provider == "openai":
            response = parser.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert en optimisation de profils candidats pour maximiser les chances de recrutement."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
        elif parser.provider == "anthropic":
            response = parser.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            import json
            result = json.loads(response.content[0].text)
        
        logger.info(f"✅ Suggestions générées pour section: {section_name}")
        
        return {
            "success": True,
            "section": section_name,
            "suggestions": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suggestions section: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
