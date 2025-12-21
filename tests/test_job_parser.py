"""
🧪 Tests pour le Service de Parsing de Fiches de Poste
========================================================
"""

import pytest
from api.services.job_description_parser_service import JobDescriptionParserService


# Exemple de fiche de poste en français
SAMPLE_JOB_FR = """
DÉVELOPPEUR FULL STACK SENIOR

TechStartup - Paris

Nous recherchons un développeur Full Stack passionné pour rejoindre notre équipe.

MISSIONS PRINCIPALES:
- Développer et maintenir notre application web
- Participer à l'architecture des solutions
- Mentorer les développeurs juniors

COMPÉTENCES REQUISES:
- JavaScript/TypeScript
- React, Node.js
- SQL, MongoDB
- Git

COMPÉTENCES BONUS:
- Docker, Kubernetes
- AWS
- Next.js

PROFIL:
- Expérience: 5-8 ans
- Diplôme: Bac+5 en informatique
- Anglais courant

SOFT SKILLS:
- Esprit d'équipe
- Autonomie
- Communication

OFFRE:
- CDI
- Salaire: 55-70k€
- Télétravail hybride (2j/semaine)
- Tickets restaurant
- Mutuelle
- RTT

Démarrage: Dès que possible
"""


# Exemple de fiche de poste en anglais
SAMPLE_JOB_EN = """
SENIOR SOFTWARE ENGINEER

Silicon Valley Tech - San Francisco, CA

We are seeking a talented Senior Software Engineer to join our growing team.

RESPONSIBILITIES:
- Design and develop scalable applications
- Lead technical initiatives
- Mentor junior developers

REQUIRED SKILLS:
- Python, Java
- Microservices architecture
- AWS, Docker
- SQL, NoSQL

QUALIFICATIONS:
- 7+ years of experience
- BS/MS in Computer Science
- Strong communication skills

COMPENSATION:
- Full-time position
- Salary: $140,000 - $180,000
- Remote friendly
- Health insurance
- 401k matching
- Unlimited PTO

Start date: Immediate
"""


def test_job_parser_initialization():
    """Test de l'initialisation du service"""
    # Note: Ce test nécessite une clé API valide
    # Pour les tests, on peut skip si pas de clé
    pytest.skip("Nécessite une clé API OpenAI ou Anthropic")


def test_supported_languages():
    """Test que les 10 langues principales sont supportées"""
    # Note: On peut tester sans clé API
    expected_languages = {"en", "zh", "hi", "es", "fr", "ar", "bn", "ru", "pt", "de"}
    
    assert JobDescriptionParserService.SUPPORTED_LANGUAGES.keys() == expected_languages
    assert len(JobDescriptionParserService.SUPPORTED_LANGUAGES) == 10


@pytest.mark.asyncio
async def test_parse_french_job():
    """Test du parsing d'une fiche de poste en français"""
    pytest.skip("Nécessite une clé API - Test d'intégration")
    
    # Ce test serait exécuté avec une vraie clé API
    # parser = JobDescriptionParserService(api_key="your-key", provider="openai")
    # result = await parser.parse_job_description_from_text(SAMPLE_JOB_FR)
    # 
    # assert result["titre_poste"] == "Développeur Full Stack Senior"
    # assert "javascript" in [c.lower() for c in result["competences_requises"]]
    # assert result["salaire_min"] >= 55000
    # assert result["salaire_max"] <= 70000


@pytest.mark.asyncio
async def test_parse_english_job():
    """Test du parsing d'une fiche de poste en anglais"""
    pytest.skip("Nécessite une clé API - Test d'intégration")


@pytest.mark.asyncio
async def test_language_detection():
    """Test de la détection automatique de langue"""
    pytest.skip("Nécessite une clé API - Test d'intégration")


@pytest.mark.asyncio
async def test_translation():
    """Test de la traduction d'une fiche de poste"""
    pytest.skip("Nécessite une clé API - Test d'intégration")


if __name__ == "__main__":
    print("🧪 Tests du Job Description Parser Service")
    print(f"✅ {len(JobDescriptionParserService.SUPPORTED_LANGUAGES)} langues supportées:")
    for code, name in JobDescriptionParserService.SUPPORTED_LANGUAGES.items():
        print(f"  - {code}: {name}")
