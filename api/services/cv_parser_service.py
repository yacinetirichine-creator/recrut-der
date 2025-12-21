"""
📄 Recrut'der - Service d'IA pour parsing de CV
================================================
Extraction automatique des informations d'un CV avec OpenAI/Claude
"""

from typing import Dict, Any, Optional, List
from fastapi import UploadFile, HTTPException
from loguru import logger
import json


class CVParserService:
    """Service de parsing de CV par IA"""
    
    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Initialiser le service de parsing CV
        
        Args:
            api_key: Clé API (OpenAI ou Anthropic)
            provider: 'openai' ou 'anthropic' (Claude)
        """
        self.api_key = api_key
        self.provider = provider
        
        if provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("pip install openai pour utiliser OpenAI")
        elif provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("pip install anthropic pour utiliser Claude")
        else:
            raise ValueError("Provider doit être 'openai' ou 'anthropic'")
    
    
    async def parse_cv_from_text(self, cv_text: str) -> Dict[str, Any]:
        """
        Parser un CV à partir du texte extrait
        
        Returns:
            Dict avec toutes les informations structurées
        """
        try:
            prompt = self._build_parsing_prompt(cv_text)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Plus économique et rapide
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un expert en extraction d'informations de CV. Tu dois extraire et structurer les données d'un CV au format JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                result = json.loads(response.content[0].text)
            
            logger.info("✅ CV parsé avec succès par IA")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing CV: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du parsing du CV: {str(e)}"
            )
    
    
    def _build_parsing_prompt(self, cv_text: str) -> str:
        """Construire le prompt pour l'IA"""
        return f"""
Analyse ce CV et extrais TOUTES les informations dans un format JSON structuré.

STRUCTURE JSON ATTENDUE (retourne exactement ce format):
{{
    "informations_personnelles": {{
        "nom": "string",
        "prenom": "string",
        "email": "string",
        "telephone": "string",
        "adresse": "string",
        "ville": "string",
        "code_postal": "string",
        "pays": "string",
        "linkedin_url": "string",
        "portfolio_url": "string",
        "photo_url": "string ou null"
    }},
    "bio": "Une bio professionnelle attractive de 2-3 phrases (à générer si absente)",
    "experiences": [
        {{
            "titre_poste": "string",
            "entreprise": "string",
            "localisation": "string",
            "date_debut": "YYYY-MM",
            "date_fin": "YYYY-MM ou 'présent'",
            "duree_mois": 12,
            "description": "string",
            "realisations": ["string", "string"],
            "technologies": ["string", "string"]
        }}
    ],
    "formations": [
        {{
            "diplome": "string",
            "niveau": "bac+3, bac+5, etc.",
            "ecole": "string",
            "ville": "string",
            "date_debut": "YYYY",
            "date_fin": "YYYY",
            "specialite": "string",
            "mention": "string ou null"
        }}
    ],
    "competences_techniques": [
        "Python", "JavaScript", "React", "SQL", "..."
    ],
    "soft_skills": [
        "Leadership", "Communication", "Travail en équipe", "..."
    ],
    "langues": [
        {{
            "langue": "Français",
            "niveau": "Natif / Courant / Intermédiaire / Notions"
        }}
    ],
    "certifications": [
        {{
            "nom": "string",
            "organisme": "string",
            "date": "YYYY-MM",
            "url": "string ou null"
        }}
    ],
    "centres_interet": ["string", "string"],
    "disponibilite": "immediate / 1_mois / 3_mois / flexible",
    "experience_totale_annees": 5,
    "salaire_souhaite_min": 45000,
    "salaire_souhaite_max": 55000,
    "type_contrat_souhaite": ["cdi", "freelance"],
    "secteurs_cibles": ["tech", "finance", "startup"],
    "taille_entreprise_preferee": ["startup", "pme"]
}}

INSTRUCTIONS IMPORTANTES:
1. Extrais toutes les informations présentes dans le CV
2. Si une info n'est pas présente, mets null ou [] selon le type
3. Pour la bio, si elle n'existe pas, génère une bio professionnelle attractive basée sur l'expérience
4. Calcule l'expérience totale en années
5. Déduis les soft skills des expériences si non mentionnés explicitement
6. Retourne UNIQUEMENT le JSON, sans texte avant ou après
7. Assure-toi que le JSON est valide et bien formaté

CV À ANALYSER:
{cv_text}
"""
    
    
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """
        Extraire le texte d'un PDF
        
        Args:
            pdf_file: Fichier PDF uploadé
            
        Returns:
            Texte extrait du PDF
        """
        try:
            import PyPDF2
            from io import BytesIO
            
            # Lire le fichier
            content = await pdf_file.read()
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            
            # Extraire le texte de toutes les pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
            
            logger.info(f"✅ Texte extrait du PDF ({len(text)} caractères)")
            return text
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction PDF: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de l'extraction du PDF: {str(e)}"
            )
    
    
    async def generate_profile_suggestions(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Générer des suggestions pour améliorer le profil candidat
        
        Args:
            cv_data: Données du CV déjà parsées
            
        Returns:
            Suggestions d'amélioration
        """
        try:
            prompt = f"""
Analyse ce profil candidat et génère des suggestions d'amélioration.

PROFIL:
{json.dumps(cv_data, ensure_ascii=False, indent=2)}

RETOURNE un JSON avec cette structure:
{{
    "score_completude": 85,
    "points_forts": [
        "Expérience solide en développement",
        "Bonnes compétences techniques",
        "..."
    ],
    "suggestions_amelioration": [
        "Ajouter plus de détails sur vos réalisations quantifiables",
        "Compléter les certifications",
        "..."
    ],
    "bio_amelioree": "Version améliorée de la bio professionnelle",
    "competences_manquantes_suggere": [
        "Docker", "Kubernetes", "..."
    ],
    "mots_cles_optimisation": [
        "Mots-clés à ajouter pour améliorer la visibilité"
    ]
}}

Retourne UNIQUEMENT le JSON.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un expert en recrutement et optimisation de profils candidats."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
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
                
                result = json.loads(response.content[0].text)
            
            logger.info("✅ Suggestions générées avec succès")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur génération suggestions: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération des suggestions: {str(e)}"
            )
    
    
    async def match_with_job_description(
        self, 
        cv_data: Dict[str, Any], 
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyser le match entre un CV et une offre d'emploi
        
        Args:
            cv_data: Données du CV
            job_description: Description de l'offre d'emploi
            
        Returns:
            Analyse du match avec score et explications
        """
        try:
            prompt = f"""
Analyse le match entre ce profil candidat et cette offre d'emploi.

PROFIL CANDIDAT:
{json.dumps(cv_data, ensure_ascii=False, indent=2)}

OFFRE D'EMPLOI:
{job_description}

RETOURNE un JSON avec cette structure:
{{
    "score_match": 85,
    "compatibilite": "Excellent / Bon / Moyen / Faible",
    "points_forts_match": [
        "Compétences techniques alignées",
        "Expérience pertinente de 5 ans",
        "..."
    ],
    "points_faibles_match": [
        "Manque d'expérience en leadership",
        "..."
    ],
    "competences_matchees": [
        "Python", "React", "..."
    ],
    "competences_manquantes": [
        "Kubernetes", "..."
    ],
    "recommandation": "Candidat hautement recommandé car...",
    "questions_suggérees_entretien": [
        "Pouvez-vous détailler votre expérience en...?",
        "..."
    ]
}}

Retourne UNIQUEMENT le JSON.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un expert en recrutement et matching candidat-offre."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                result = json.loads(response.content[0].text)
            
            logger.info("✅ Analyse de match générée avec succès")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse match: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'analyse du match: {str(e)}"
            )
