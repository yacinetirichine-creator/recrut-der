"""
📄 Recrut'der - Service d'IA pour parsing de Fiche de Poste
============================================================
Extraction automatique des informations d'une fiche de poste avec OpenAI/Claude
Support multilingue: Anglais, Chinois, Hindi, Espagnol, Français, Arabe, Bengali, Russe, Portugais, Allemand
"""

from typing import Dict, Any, Optional, List
from fastapi import UploadFile, HTTPException
from loguru import logger
import json


class JobDescriptionParserService:
    """Service de parsing de fiche de poste par IA avec support multilingue"""
    
    # Top 10 des langues les plus parlées au monde
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "zh": "中文 (Chinese)",
        "hi": "हिन्दी (Hindi)",
        "es": "Español",
        "fr": "Français",
        "ar": "العربية (Arabic)",
        "bn": "বাংলা (Bengali)",
        "ru": "Русский (Russian)",
        "pt": "Português",
        "de": "Deutsch"
    }
    
    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Initialiser le service de parsing de fiche de poste
        
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
    
    
    async def detect_language(self, text: str) -> str:
        """
        Détecter la langue du texte
        
        Args:
            text: Texte de la fiche de poste
            
        Returns:
            Code de langue (en, fr, es, etc.)
        """
        try:
            prompt = f"""
Détecte la langue de ce texte et retourne UNIQUEMENT le code ISO 639-1 (2 lettres).

Codes possibles: en, zh, hi, es, fr, ar, bn, ru, pt, de

Texte à analyser:
{text[:500]}

Retourne UNIQUEMENT le code de langue, rien d'autre.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0,
                    max_tokens=10
                )
                
                lang_code = response.choices[0].message.content.strip().lower()
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                lang_code = response.content[0].text.strip().lower()
            
            # Valider le code de langue
            if lang_code not in self.SUPPORTED_LANGUAGES:
                logger.warning(f"⚠️ Langue non reconnue: {lang_code}, utilisation du français par défaut")
                lang_code = "fr"
            
            logger.info(f"✅ Langue détectée: {self.SUPPORTED_LANGUAGES[lang_code]} ({lang_code})")
            return lang_code
            
        except Exception as e:
            logger.error(f"❌ Erreur détection langue: {e}")
            return "fr"  # Fallback vers le français
    
    
    async def parse_job_description_from_text(
        self, 
        job_text: str, 
        auto_detect_language: bool = True,
        target_language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Parser une fiche de poste à partir du texte extrait
        
        Args:
            job_text: Texte de la fiche de poste
            auto_detect_language: Détecter automatiquement la langue
            target_language: Langue cible pour la sortie (par défaut: français)
            
        Returns:
            Dict avec toutes les informations structurées
        """
        try:
            # Détecter la langue si demandé
            detected_lang = "fr"
            if auto_detect_language:
                detected_lang = await self.detect_language(job_text)
            
            prompt = self._build_parsing_prompt(job_text, detected_lang, target_language)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un expert en extraction d'informations de fiches de poste. Tu dois extraire et structurer les données au format JSON."
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
            
            # Ajouter les métadonnées de langue
            result["langue_source"] = detected_lang
            result["langue_cible"] = target_language
            
            logger.info("✅ Fiche de poste parsée avec succès par IA")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing fiche de poste: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du parsing de la fiche de poste: {str(e)}"
            )
    
    
    def _build_parsing_prompt(self, job_text: str, source_lang: str, target_lang: str) -> str:
        """Construire le prompt pour l'IA"""
        
        translation_instruction = ""
        if source_lang != target_lang:
            translation_instruction = f"""
⚠️ IMPORTANT: La fiche de poste est en {self.SUPPORTED_LANGUAGES.get(source_lang, source_lang)}.
Tu dois TRADUIRE toutes les informations en {self.SUPPORTED_LANGUAGES.get(target_lang, target_lang)} dans le JSON de sortie.
"""
        
        return f"""
Analyse cette fiche de poste et extrais TOUTES les informations dans un format JSON structuré.

{translation_instruction}

STRUCTURE JSON ATTENDUE (retourne exactement ce format):
{{
    "titre_poste": "string",
    "entreprise": "string (si mentionné)",
    "description_complete": "string - Description complète et attractive du poste",
    "description_courte": "string - Résumé en 2-3 phrases",
    
    "competences_requises": [
        "Compétence technique 1", "Compétence technique 2", "..."
    ],
    "competences_bonus": [
        "Compétence nice-to-have 1", "..."
    ],
    "soft_skills_recherches": [
        "Communication", "Leadership", "Travail en équipe", "..."
    ],
    
    "experience_min": 3,
    "experience_max": 5,
    
    "qualifications_requises": [
        "Diplôme requis", "Certification requise", "..."
    ],
    "qualifications_bonus": [
        "Diplôme bonus", "..."
    ],
    "niveau_etudes_min": "bac+3 / bac+5 / bac+8",
    
    "salaire_min": 45000,
    "salaire_max": 55000,
    "salaire_devise": "EUR / USD / GBP / etc.",
    "salaire_periode": "annuel / mensuel",
    
    "localisation": "Ville, Pays",
    "ville": "Paris",
    "pays": "France",
    "code_postal": "75001",
    "remote_possible": true,
    "politique_teletravail": "full_remote / hybride / presentiel",
    
    "secteur": "tech / finance / marketing / etc.",
    "type_contrat": "cdi / cdd / freelance / stage / alternance",
    "date_debut_souhaitee": "immediate / 1_mois / 3_mois / flexible",
    
    "langues_requises": [
        "Français", "Anglais", "..."
    ],
    "langues_bonus": [
        "Allemand", "..."
    ],
    
    "taille_entreprise": "startup / pme / grand_groupe",
    
    "avantages": [
        "Tickets restaurant", "Mutuelle", "RTT", "..."
    ],
    
    "responsabilites": [
        "Responsabilité 1", "Responsabilité 2", "..."
    ],
    
    "missions_principales": [
        "Mission 1", "Mission 2", "..."
    ],
    
    "processus_recrutement": {{
        "etapes": ["Entretien RH", "Entretien technique", "..."],
        "duree_estimee": "2 semaines / 1 mois / etc."
    }},
    
    "contact": {{
        "email": "string ou null",
        "telephone": "string ou null",
        "site_web": "string ou null"
    }}
}}

INSTRUCTIONS IMPORTANTES:
1. Extrais toutes les informations présentes dans la fiche de poste
2. Si une info n'est pas présente, mets null ou [] selon le type
3. Pour les salaires, convertis en chiffres (ex: "45k€" → 45000)
4. Déduis le secteur, la taille d'entreprise si possible
5. Sépare bien les compétences "requises" (must-have) des "bonus" (nice-to-have)
6. Identifie les soft skills recherchés même s'ils ne sont pas explicitement listés
7. Retourne UNIQUEMENT le JSON, sans texte avant ou après
8. Assure-toi que le JSON est valide et bien formaté
{translation_instruction and "9. TRADUIS tout le contenu en " + self.SUPPORTED_LANGUAGES.get(target_lang, target_lang) or ""}

FICHE DE POSTE À ANALYSER:
{job_text}
"""
    
    
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """
        Extraire le texte d'un PDF de fiche de poste
        
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
    
    
    async def extract_text_from_docx(self, docx_file: UploadFile) -> str:
        """
        Extraire le texte d'un fichier DOCX de fiche de poste
        
        Args:
            docx_file: Fichier DOCX uploadé
            
        Returns:
            Texte extrait du DOCX
        """
        try:
            import docx
            from io import BytesIO
            
            # Lire le fichier
            content = await docx_file.read()
            doc = docx.Document(BytesIO(content))
            
            # Extraire le texte de tous les paragraphes
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            logger.info(f"✅ Texte extrait du DOCX ({len(text)} caractères)")
            return text
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction DOCX: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de l'extraction du DOCX: {str(e)}"
            )
    
    
    async def improve_job_description(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Générer des suggestions pour améliorer la fiche de poste
        
        Args:
            job_data: Données de la fiche de poste déjà parsées
            
        Returns:
            Suggestions d'amélioration et version optimisée
        """
        try:
            prompt = f"""
Analyse cette fiche de poste et génère des suggestions d'amélioration pour attirer les meilleurs candidats.

FICHE DE POSTE ACTUELLE:
{json.dumps(job_data, ensure_ascii=False, indent=2)}

RETOURNE un JSON avec cette structure:
{{
    "score_qualite": 75,
    "points_forts": [
        "Description claire des responsabilités",
        "Salaire compétitif",
        "..."
    ],
    "suggestions_amelioration": [
        "Ajouter des informations sur la culture d'entreprise",
        "Préciser les avantages sociaux",
        "Détailler les opportunités d'évolution",
        "..."
    ],
    "description_amelioree": "Version améliorée de la description complète",
    "description_courte_amelioree": "Version optimisée du résumé attractif",
    "titres_alternatifs": [
        "Titre alternatif 1 plus attractif",
        "Titre alternatif 2",
        "..."
    ],
    "competences_supplementaires_suggere": [
        "Compétence pertinente 1", "..."
    ],
    "mots_cles_seo": [
        "Mots-clés pour améliorer la visibilité de l'offre"
    ],
    "conseils_attraction_candidats": [
        "Conseil 1", "Conseil 2", "..."
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
                            "content": "Tu es un expert en recrutement et rédaction d'offres d'emploi attractives."
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
                    max_tokens=3000,
                    temperature=0.3,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                result = json.loads(response.content[0].text)
            
            logger.info("✅ Suggestions d'amélioration générées avec succès")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur génération suggestions: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération des suggestions: {str(e)}"
            )
    
    
    async def translate_job_description(
        self, 
        job_data: Dict[str, Any], 
        target_language: str
    ) -> Dict[str, Any]:
        """
        Traduire une fiche de poste dans une autre langue
        
        Args:
            job_data: Données de la fiche de poste
            target_language: Langue cible (code ISO: en, es, de, etc.)
            
        Returns:
            Fiche de poste traduite
        """
        try:
            if target_language not in self.SUPPORTED_LANGUAGES:
                raise ValueError(f"Langue non supportée: {target_language}")
            
            target_lang_name = self.SUPPORTED_LANGUAGES[target_language]
            
            prompt = f"""
Traduis cette fiche de poste complète en {target_lang_name}.

FICHE DE POSTE À TRADUIRE:
{json.dumps(job_data, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Traduis TOUS les champs textuels en {target_lang_name}
2. Conserve la même structure JSON
3. Ne traduis PAS les codes (type_contrat, politique_teletravail, etc.)
4. Adapte culturellement si nécessaire (ex: salaires, avantages)
5. Conserve les chiffres (salaire, expérience, etc.)

Retourne le JSON complet traduit.
"""
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": f"Tu es un traducteur professionnel spécialisé en recrutement. Traduis en {target_lang_name}."
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
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                result = json.loads(response.content[0].text)
            
            result["langue_cible"] = target_language
            
            logger.info(f"✅ Fiche de poste traduite en {target_lang_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur traduction: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la traduction: {str(e)}"
            )
