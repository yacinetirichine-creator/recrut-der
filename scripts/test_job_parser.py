"""
📄 Script de Test - Parsing de Fiche de Poste avec IA
======================================================
Test manuel du service de parsing de fiches de poste
Support multilingue: 10 langues principales
"""

import asyncio
import os
from api.services.job_description_parser_service import JobDescriptionParserService


# Exemple de fiche de poste en français
SAMPLE_JOB_FR = """
DÉVELOPPEUR FULL STACK SENIOR

TechStartup - Paris, 75001

Nous recherchons un développeur Full Stack passionné pour rejoindre notre équipe de 20 personnes.

MISSIONS PRINCIPALES:
- Développer et maintenir notre application SaaS
- Participer à l'architecture des solutions techniques
- Mentorer les développeurs juniors
- Participer aux code reviews

COMPÉTENCES REQUISES:
- JavaScript/TypeScript
- React, Node.js
- PostgreSQL, MongoDB
- Git, CI/CD

COMPÉTENCES BONUS:
- Docker, Kubernetes
- AWS ou GCP
- Next.js, GraphQL

PROFIL RECHERCHÉ:
- Expérience: 5-8 ans en développement web
- Diplôme: Bac+5 en informatique ou école d'ingénieur
- Anglais courant requis

SOFT SKILLS:
- Esprit d'équipe
- Autonomie
- Excellente communication
- Curiosité technique

NOTRE OFFRE:
- CDI
- Salaire: 55 000 - 70 000€ brut annuel
- Télétravail hybride (2-3 jours/semaine)
- Tickets restaurant (11€/jour)
- Mutuelle prise en charge à 100%
- 12 jours de RTT
- Budget formation (2000€/an)

Date de démarrage souhaitée: Dès que possible

Pour postuler: jobs@techstartup.fr
"""


# Exemple de fiche de poste en anglais
SAMPLE_JOB_EN = """
SENIOR SOFTWARE ENGINEER

TechCorp - San Francisco, CA 94102

We're looking for an experienced Senior Software Engineer to join our platform team.

RESPONSIBILITIES:
- Design and build scalable microservices
- Lead technical architecture decisions
- Mentor junior engineers
- Participate in on-call rotation

REQUIRED SKILLS:
- Python, Java, or Go
- Microservices architecture
- AWS, Docker, Kubernetes
- SQL and NoSQL databases
- REST and GraphQL APIs

QUALIFICATIONS:
- 7+ years of software engineering experience
- BS/MS in Computer Science or equivalent
- Strong problem-solving skills
- Excellent written and verbal communication

NICE TO HAVE:
- Experience with event-driven architectures
- ML/AI experience
- Open source contributions

COMPENSATION & BENEFITS:
- Full-time position
- Salary: $140,000 - $180,000 per year
- Remote-friendly (hybrid 2 days/week)
- Comprehensive health insurance
- 401k with company match
- Unlimited PTO
- $2,500 annual learning budget

Start date: Immediate

Apply: careers@techcorp.com
"""


async def test_french_job_parsing():
    """Test du parsing d'une fiche de poste en français"""
    print("\n" + "="*80)
    print("🇫🇷 TEST 1: Parsing d'une fiche de poste en FRANÇAIS")
    print("="*80)
    
    # Récupérer la clé API depuis les variables d'environnement
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("❌ Aucune clé API trouvée. Ajoutez OPENAI_API_KEY ou ANTHROPIC_API_KEY dans .env")
        return
    
    # Initialiser le service
    provider = "openai" if openai_key else "anthropic"
    api_key = openai_key if openai_key else anthropic_key
    
    parser = JobDescriptionParserService(api_key=api_key, provider=provider)
    print(f"✅ Service initialisé avec {provider}")
    
    # Parser la fiche de poste
    print("\n📄 Parsing de la fiche de poste...")
    result = await parser.parse_job_description_from_text(
        job_text=SAMPLE_JOB_FR,
        auto_detect_language=True,
        target_language="fr"
    )
    
    # Afficher les résultats
    print("\n📊 RÉSULTATS DU PARSING:")
    print(f"  Titre: {result.get('titre_poste')}")
    print(f"  Entreprise: {result.get('entreprise')}")
    print(f"  Localisation: {result.get('localisation')}")
    print(f"  Salaire: {result.get('salaire_min'):,} - {result.get('salaire_max'):,} {result.get('salaire_devise')}")
    print(f"  Expérience: {result.get('experience_min')}-{result.get('experience_max')} ans")
    print(f"  Type contrat: {result.get('type_contrat')}")
    print(f"  Télétravail: {result.get('politique_teletravail')}")
    print(f"  Langue source: {result.get('langue_source')}")
    print(f"  Langue cible: {result.get('langue_cible')}")
    
    print(f"\n  Compétences requises ({len(result.get('competences_requises', []))}):")
    for comp in result.get('competences_requises', [])[:5]:
        print(f"    - {comp}")
    
    print(f"\n  Soft skills ({len(result.get('soft_skills_recherches', []))}):")
    for skill in result.get('soft_skills_recherches', []):
        print(f"    - {skill}")
    
    print(f"\n  Avantages ({len(result.get('avantages', []))}):")
    for avantage in result.get('avantages', []):
        print(f"    - {avantage}")
    
    print(f"\n  Description courte:")
    print(f"    {result.get('description_courte')}")
    
    return result


async def test_english_job_parsing_with_translation():
    """Test du parsing d'une fiche en anglais avec traduction en français"""
    print("\n" + "="*80)
    print("🇬🇧 TEST 2: Parsing d'une fiche ANGLAISE + Traduction en FRANÇAIS")
    print("="*80)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("❌ Aucune clé API trouvée")
        return
    
    provider = "openai" if openai_key else "anthropic"
    api_key = openai_key if openai_key else anthropic_key
    
    parser = JobDescriptionParserService(api_key=api_key, provider=provider)
    print(f"✅ Service initialisé avec {provider}")
    
    # Parser avec détection auto et traduction
    print("\n📄 Parsing et traduction automatique...")
    result = await parser.parse_job_description_from_text(
        job_text=SAMPLE_JOB_EN,
        auto_detect_language=True,
        target_language="fr"  # Traduire en français
    )
    
    print("\n📊 RÉSULTATS (traduit en français):")
    print(f"  Titre: {result.get('titre_poste')}")
    print(f"  Entreprise: {result.get('entreprise')}")
    print(f"  Localisation: {result.get('localisation')}")
    print(f"  Salaire: ${result.get('salaire_min'):,} - ${result.get('salaire_max'):,}")
    print(f"  Langue détectée: {result.get('langue_source')} (Anglais)")
    print(f"  Traduit en: {result.get('langue_cible')} (Français)")
    
    print(f"\n  Description courte (traduite):")
    print(f"    {result.get('description_courte')}")
    
    return result


async def test_improvement_suggestions():
    """Test des suggestions d'amélioration"""
    print("\n" + "="*80)
    print("💡 TEST 3: Suggestions d'amélioration")
    print("="*80)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("❌ Aucune clé API trouvée")
        return
    
    provider = "openai" if openai_key else "anthropic"
    api_key = openai_key if openai_key else anthropic_key
    
    parser = JobDescriptionParserService(api_key=api_key, provider=provider)
    
    # D'abord parser une fiche
    result = await parser.parse_job_description_from_text(
        job_text=SAMPLE_JOB_FR,
        auto_detect_language=True,
        target_language="fr"
    )
    
    # Demander des suggestions
    print("\n💡 Génération de suggestions d'amélioration...")
    suggestions = await parser.improve_job_description(result)
    
    print("\n📊 SUGGESTIONS:")
    print(f"  Score qualité: {suggestions.get('score_qualite')}/100")
    
    print(f"\n  ✅ Points forts:")
    for point in suggestions.get('points_forts', [])[:3]:
        print(f"    - {point}")
    
    print(f"\n  📝 Suggestions d'amélioration:")
    for sugg in suggestions.get('suggestions_amelioration', [])[:3]:
        print(f"    - {sugg}")
    
    print(f"\n  🔑 Mots-clés SEO suggérés:")
    for keyword in suggestions.get('mots_cles_seo', [])[:5]:
        print(f"    - {keyword}")


async def test_supported_languages():
    """Test des langues supportées"""
    print("\n" + "="*80)
    print("🌍 TEST 4: Langues supportées")
    print("="*80)
    
    print(f"\n📋 {len(JobDescriptionParserService.SUPPORTED_LANGUAGES)} langues supportées:")
    for i, (code, name) in enumerate(JobDescriptionParserService.SUPPORTED_LANGUAGES.items(), 1):
        print(f"  {i}. {code.upper()}: {name}")


async def main():
    """Fonction principale de test"""
    print("\n" + "="*80)
    print("🚀 TESTS DU SERVICE DE PARSING DE FICHES DE POSTE")
    print("="*80)
    
    # Test 1: Parser une fiche française
    try:
        await test_french_job_parsing()
    except Exception as e:
        print(f"❌ Erreur Test 1: {e}")
    
    # Test 2: Parser une fiche anglaise et traduire
    try:
        await test_english_job_parsing_with_translation()
    except Exception as e:
        print(f"❌ Erreur Test 2: {e}")
    
    # Test 3: Suggestions d'amélioration
    try:
        await test_improvement_suggestions()
    except Exception as e:
        print(f"❌ Erreur Test 3: {e}")
    
    # Test 4: Langues supportées
    await test_supported_languages()
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
