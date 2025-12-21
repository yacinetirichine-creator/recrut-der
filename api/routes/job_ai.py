"""
📄 Recrut'der - Routes IA pour Fiches de Poste
===============================================
Upload, parsing automatique et suggestions IA pour les fiches de poste
Support multilingue: Anglais, Chinois, Hindi, Espagnol, Français, Arabe, Bengali, Russe, Portugais, Allemand
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Dict, Any, Optional
from uuid import UUID

from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from api.services.job_description_parser_service import JobDescriptionParserService
from api.config import settings
from loguru import logger


router = APIRouter()

# Initialiser le service Job Description Parser
job_parser = None

def get_job_parser() -> JobDescriptionParserService:
    """Obtenir le service de parsing de fiche de poste"""
    global job_parser
    
    if job_parser is None:
        # Vérifier si une clé API IA est configurée
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        
        if openai_key:
            job_parser = JobDescriptionParserService(api_key=openai_key, provider="openai")
            logger.info("✅ Service Job Description Parser initialisé avec OpenAI")
        elif anthropic_key:
            job_parser = JobDescriptionParserService(api_key=anthropic_key, provider="anthropic")
            logger.info("✅ Service Job Description Parser initialisé avec Claude")
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service d'IA non configuré. Ajoutez OPENAI_API_KEY ou ANTHROPIC_API_KEY dans .env"
            )
    
    return job_parser


@router.post("/upload-job-description")
async def upload_and_parse_job_description(
    file: UploadFile = File(...),
    auto_detect_language: bool = Form(True),
    target_language: str = Form("fr"),
    current_user: dict = Depends(get_current_user)
):
    """
    📤 Upload et parsing automatique d'une fiche de poste (PDF/DOCX/TXT)
    
    Workflow:
    1. Upload le fichier (PDF, DOCX ou TXT)
    2. Extrait le texte
    3. Détecte automatiquement la langue (si activé)
    4. Parse avec l'IA et traduit si nécessaire
    5. Retourne les données structurées
    
    Le recruteur pourra ensuite valider/modifier chaque section avant publication
    
    Args:
        file: Fichier de la fiche de poste (PDF, DOCX, TXT)
        auto_detect_language: Détection automatique de la langue (défaut: True)
        target_language: Langue cible pour la sortie (défaut: "fr")
        
    Langues supportées: en, zh, hi, es, fr, ar, bn, ru, pt, de
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent uploader des fiches de poste"
            )
        
        # Obtenir le service de parsing
        parser = get_job_parser()
        
        # Vérifier le type de fichier et extraire le texte
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith('.pdf'):
            job_text = await parser.extract_text_from_pdf(file)
        elif filename_lower.endswith('.docx'):
            job_text = await parser.extract_text_from_docx(file)
        elif filename_lower.endswith('.txt'):
            content = await file.read()
            job_text = content.decode('utf-8')
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format de fichier non supporté. Utilisez PDF, DOCX ou TXT"
            )
        
        logger.info(f"📄 Fichier uploadé: {file.filename} ({len(job_text)} caractères)")
        
        # Parser la fiche de poste avec l'IA
        parsed_data = await parser.parse_job_description_from_text(
            job_text=job_text,
            auto_detect_language=auto_detect_language,
            target_language=target_language
        )
        
        # Ajouter des métadonnées
        parsed_data["fichier_original"] = file.filename
        parsed_data["recruteur_id"] = recruteur.data["id"]
        
        logger.info("✅ Fiche de poste parsée avec succès")
        
        return {
            "success": True,
            "message": "Fiche de poste analysée avec succès",
            "data": parsed_data,
            "langue_detectee": parsed_data.get("langue_source"),
            "langue_sortie": parsed_data.get("langue_cible")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur upload/parsing fiche de poste: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement de la fiche de poste: {str(e)}"
        )


@router.post("/parse-job-text")
async def parse_job_from_text(
    job_text: str = Form(...),
    auto_detect_language: bool = Form(True),
    target_language: str = Form("fr"),
    current_user: dict = Depends(get_current_user)
):
    """
    📝 Parser une fiche de poste à partir de texte brut (copier-coller)
    
    Alternative à l'upload de fichier pour les recruteurs qui veulent
    simplement copier-coller le texte de leur fiche de poste
    
    Args:
        job_text: Texte de la fiche de poste
        auto_detect_language: Détection automatique de la langue
        target_language: Langue cible pour la sortie
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent parser des fiches de poste"
            )
        
        # Obtenir le service de parsing
        parser = get_job_parser()
        
        # Parser la fiche de poste avec l'IA
        parsed_data = await parser.parse_job_description_from_text(
            job_text=job_text,
            auto_detect_language=auto_detect_language,
            target_language=target_language
        )
        
        # Ajouter des métadonnées
        parsed_data["recruteur_id"] = recruteur.data["id"]
        
        logger.info("✅ Fiche de poste parsée avec succès depuis texte")
        
        return {
            "success": True,
            "message": "Fiche de poste analysée avec succès",
            "data": parsed_data,
            "langue_detectee": parsed_data.get("langue_source"),
            "langue_sortie": parsed_data.get("langue_cible")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur parsing texte fiche de poste: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de la fiche de poste: {str(e)}"
        )


@router.post("/validate-and-create-offer")
async def validate_and_create_offer(
    job_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Valider et créer une offre d'emploi à partir des données parsées
    
    Le recruteur peut avoir modifié les données parsées avant de les soumettre.
    Cette route crée l'offre dans la base de données.
    
    Args:
        job_data: Données de la fiche de poste (parsées et éventuellement modifiées)
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*, entreprises!inner(*)")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent créer des offres"
            )
        
        # Vérifier qu'une entreprise existe
        if not recruteur.data.get("entreprises"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Veuillez d'abord créer votre entreprise avant de publier une offre"
            )
        
        entreprise = recruteur.data["entreprises"]
        
        # Préparer les données pour l'insertion
        offre_data = {
            "recruteur_id": recruteur.data["id"],
            "entreprise_id": entreprise["id"],
            "titre": job_data.get("titre_poste"),
            "description": job_data.get("description_complete"),
            "description_courte": job_data.get("description_courte"),
            "competences_requises": job_data.get("competences_requises", []),
            "competences_bonus": job_data.get("competences_bonus", []),
            "soft_skills_recherches": job_data.get("soft_skills_recherches", []),
            "experience_min": job_data.get("experience_min", 0),
            "experience_max": job_data.get("experience_max", 0),
            "qualifications_requises": job_data.get("qualifications_requises", []),
            "qualifications_bonus": job_data.get("qualifications_bonus", []),
            "niveau_etudes_min": job_data.get("niveau_etudes_min", "bac+3"),
            "salaire_min": job_data.get("salaire_min", 0),
            "salaire_max": job_data.get("salaire_max", 0),
            "localisation": job_data.get("localisation"),
            "ville": job_data.get("ville"),
            "pays": job_data.get("pays", "France"),
            "code_postal": job_data.get("code_postal"),
            "remote_possible": job_data.get("remote_possible", False),
            "politique_teletravail": job_data.get("politique_teletravail", "hybride"),
            "secteur": job_data.get("secteur"),
            "type_contrat": job_data.get("type_contrat", "cdi"),
            "date_debut_souhaitee": job_data.get("date_debut_souhaitee", "1_mois"),
            "langues_requises": job_data.get("langues_requises", ["français"]),
            "langues_bonus": job_data.get("langues_bonus", []),
            "avantages": job_data.get("avantages", []),
            "responsabilites": job_data.get("responsabilites", []),
            "missions_principales": job_data.get("missions_principales", []),
            "statut": "publiee",  # Publier directement
            "langue": job_data.get("langue_cible", "fr")
        }
        
        # Créer l'offre dans Supabase
        result = supabase.table("offres").insert(offre_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la création de l'offre"
            )
        
        logger.info(f"✅ Offre créée avec succès: {result.data[0]['id']}")
        
        return {
            "success": True,
            "message": "Offre créée avec succès",
            "offre": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création offre: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'offre: {str(e)}"
        )


@router.post("/improve-job-description")
async def improve_job_description(
    job_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    💡 Obtenir des suggestions pour améliorer une fiche de poste
    
    Analyse la fiche de poste et propose:
    - Score de qualité
    - Points forts / Points à améliorer
    - Version améliorée de la description
    - Mots-clés SEO
    - Conseils pour attirer les candidats
    
    Args:
        job_data: Données de la fiche de poste
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent utiliser cette fonctionnalité"
            )
        
        # Obtenir le service de parsing
        parser = get_job_parser()
        
        # Générer les suggestions d'amélioration
        suggestions = await parser.improve_job_description(job_data)
        
        logger.info("✅ Suggestions d'amélioration générées")
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur génération suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des suggestions: {str(e)}"
        )


@router.post("/translate-job-description")
async def translate_job_description(
    job_data: Dict[str, Any],
    target_language: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    🌍 Traduire une fiche de poste dans une autre langue
    
    Permet de publier la même offre en plusieurs langues pour toucher
    un public international.
    
    Args:
        job_data: Données de la fiche de poste
        target_language: Code de langue cible (en, es, de, zh, hi, ar, bn, ru, pt)
        
    Langues supportées:
    - en: Anglais
    - zh: Chinois
    - hi: Hindi
    - es: Espagnol
    - fr: Français
    - ar: Arabe
    - bn: Bengali
    - ru: Russe
    - pt: Portugais
    - de: Allemand
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent utiliser cette fonctionnalité"
            )
        
        # Obtenir le service de parsing
        parser = get_job_parser()
        
        # Traduire la fiche de poste
        translated_data = await parser.translate_job_description(
            job_data=job_data,
            target_language=target_language
        )
        
        logger.info(f"✅ Fiche de poste traduite en {target_language}")
        
        return {
            "success": True,
            "message": f"Fiche de poste traduite en {parser.SUPPORTED_LANGUAGES[target_language]}",
            "data": translated_data,
            "langue_cible": target_language
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur traduction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la traduction: {str(e)}"
        )


@router.get("/supported-languages")
async def get_supported_languages():
    """
    🌐 Liste des langues supportées pour les fiches de poste
    
    Returns:
        Dict avec les codes de langue et leurs noms
    """
    parser = get_job_parser()
    
    return {
        "success": True,
        "languages": parser.SUPPORTED_LANGUAGES,
        "total": len(parser.SUPPORTED_LANGUAGES)
    }


@router.patch("/update-offer-section/{offre_id}")
async def update_offer_section(
    offre_id: str,
    section_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    ✏️ Mise à jour partielle d'une offre (section par section)
    
    Permet au recruteur de modifier une section spécifique de l'offre
    sans tout re-sauvegarder. Parfait pour peaufiner après le parsing IA.
    
    Exemples de sections:
    - titre: "Développeur Full Stack Senior"
    - salaire_min: 55000
    - competences_requises: ["Python", "React", ...]
    - description: "..."
    - etc.
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent modifier des offres"
            )
        
        # Vérifier que l'offre appartient au recruteur
        offre = supabase.table("offres")\
            .select("*")\
            .eq("id", offre_id)\
            .eq("recruteur_id", recruteur.data["id"])\
            .single()\
            .execute()
        
        if not offre.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre non trouvée ou non autorisée"
            )
        
        # Valider que les champs existent
        allowed_fields = [
            "titre", "description", "description_courte",
            "competences_requises", "competences_bonus", "soft_skills_recherches",
            "experience_min", "experience_max",
            "qualifications_requises", "qualifications_bonus", "niveau_etudes_min",
            "salaire_min", "salaire_max",
            "localisation", "ville", "pays", "code_postal",
            "remote_possible", "politique_teletravail",
            "secteur", "type_contrat", "date_debut_souhaitee",
            "langues_requises", "langues_bonus",
            "avantages", "responsabilites", "missions_principales",
            "langue", "statut"
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
        result = supabase.table("offres")\
            .update(update_data)\
            .eq("id", offre_id)\
            .execute()
        
        logger.info(f"✅ Offre {offre_id} mise à jour: {list(update_data.keys())}")
        
        return {
            "success": True,
            "message": f"{len(update_data)} champ(s) mis à jour",
            "updated_fields": list(update_data.keys()),
            "offre_id": offre_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour offre: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/improve-offer-section/{offre_id}")
async def improve_offer_section(
    offre_id: str,
    section_name: str,
    section_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    💡 Obtenir des suggestions IA pour améliorer une section d'offre
    
    Le recruteur peut demander des conseils pour améliorer:
    - Le titre de l'offre
    - La description
    - Les compétences recherchées
    - Les avantages proposés
    - etc.
    
    Args:
        offre_id: ID de l'offre
        section_name: Nom de la section (titre, description, competences, etc.)
        section_data: Données actuelles de la section
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent utiliser cette fonctionnalité"
            )
        
        # Vérifier que l'offre appartient au recruteur
        offre = supabase.table("offres")\
            .select("*")\
            .eq("id", offre_id)\
            .eq("recruteur_id", recruteur.data["id"])\
            .single()\
            .execute()
        
        if not offre.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre non trouvée"
            )
        
        parser = get_job_parser()
        
        # Construire un prompt personnalisé selon la section
        prompt = f"""
Analyse cette section de l'offre d'emploi et donne des suggestions d'amélioration.

SECTION: {section_name}
DONNÉES ACTUELLES:
{section_data}

CONTEXTE DE L'OFFRE:
- Titre: {offre.data.get('titre')}
- Entreprise: {offre.data.get('entreprise')}
- Secteur: {offre.data.get('secteur')}
- Salaire: {offre.data.get('salaire_min')}-{offre.data.get('salaire_max')}€
- Type: {offre.data.get('type_contrat')}

RETOURNE un JSON avec:
{{
    "score_actuel": 75,
    "points_forts": ["...", "..."],
    "suggestions": ["...", "..."],
    "version_amelioree": "Version améliorée de la section",
    "exemples": ["Exemple 1", "Exemple 2"],
    "mots_cles_manquants": ["mot-clé 1", "..."],
    "conseil_attractivite": "Conseil pour rendre l'offre plus attractive"
}}

Sois précis, constructif et orienté vers l'attraction des meilleurs candidats.
"""
        
        if parser.provider == "openai":
            response = parser.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert en rédaction d'offres d'emploi attractives et optimisées pour le recrutement."
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
        
        logger.info(f"✅ Suggestions générées pour offre {offre_id}, section: {section_name}")
        
        return {
            "success": True,
            "offre_id": offre_id,
            "section": section_name,
            "suggestions": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suggestions section offre: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/offer-completeness/{offre_id}")
async def get_offer_completeness(
    offre_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Calculer le % de complétude d'une offre d'emploi
    
    Aide le recruteur à savoir quelles informations manquent pour
    avoir une offre complète et attractive.
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent accéder à cette fonctionnalité"
            )
        
        # Récupérer l'offre
        offre = supabase.table("offres")\
            .select("*")\
            .eq("id", offre_id)\
            .eq("recruteur_id", recruteur.data["id"])\
            .single()\
            .execute()
        
        if not offre.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre non trouvée"
            )
        
        data = offre.data
        total_fields = 0
        completed_fields = 0
        sections_manquantes = []
        sections_optionnelles = []
        
        # Champs obligatoires
        required_checks = {
            "Titre": bool(data.get("titre")),
            "Description": bool(data.get("description")),
            "Compétences requises": len(data.get("competences_requises", [])) > 0,
            "Expérience minimale": data.get("experience_min") is not None,
            "Salaire": data.get("salaire_min", 0) > 0 and data.get("salaire_max", 0) > 0,
            "Localisation": bool(data.get("localisation")),
            "Type de contrat": bool(data.get("type_contrat")),
        }
        
        # Champs optionnels mais recommandés
        optional_checks = {
            "Description courte": bool(data.get("description_courte")),
            "Compétences bonus": len(data.get("competences_bonus", [])) > 0,
            "Soft skills": len(data.get("soft_skills_recherches", [])) > 0,
            "Avantages": len(data.get("avantages", [])) > 0,
            "Responsabilités": len(data.get("responsabilites", [])) > 0,
            "Missions principales": len(data.get("missions_principales", [])) > 0,
            "Ville précise": bool(data.get("ville")),
        }
        
        # Calculer la complétude des champs obligatoires
        for section, is_complete in required_checks.items():
            total_fields += 1
            if is_complete:
                completed_fields += 1
            else:
                sections_manquantes.append(section)
        
        # Vérifier les champs optionnels
        for section, is_complete in optional_checks.items():
            if not is_complete:
                sections_optionnelles.append(section)
        
        completude = int((completed_fields / total_fields) * 100)
        
        # Calculer un score de qualité global (incluant optionnels)
        total_with_optional = total_fields + len(optional_checks)
        completed_with_optional = completed_fields + sum(1 for v in optional_checks.values() if v)
        score_qualite = int((completed_with_optional / total_with_optional) * 100)
        
        return {
            "offre_id": offre_id,
            "completude_obligatoire": completude,
            "score_qualite_global": score_qualite,
            "sections_manquantes": sections_manquantes,
            "sections_optionnelles_manquantes": sections_optionnelles,
            "statut": data.get("statut", "brouillon"),
            "pret_publication": completude == 100
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur calcul complétude offre: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
