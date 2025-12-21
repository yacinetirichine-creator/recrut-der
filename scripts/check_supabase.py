"""
Script de vérification de la configuration Supabase
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database.supabase_client import supabase
from api.config import settings

def check_supabase_connection():
    """Vérifie la connexion et les tables Supabase"""
    
    print("=" * 60)
    print("🔍 VÉRIFICATION CONFIGURATION SUPABASE")
    print("=" * 60)
    
    # 1. Vérifier la configuration
    print("\n📋 Configuration:")
    print(f"   URL: {settings.SUPABASE_URL}")
    print(f"   Key configurée: {'✅ Oui' if settings.SUPABASE_KEY else '❌ Non'}")
    print(f"   Service Key: {'✅ Oui' if settings.SUPABASE_SERVICE_KEY else '❌ Non'}")
    
    # 2. Tester la connexion
    print("\n🔌 Test de connexion:")
    try:
        # Essayer de lister les tables via une requête simple
        result = supabase.table("utilisateurs").select("*").limit(0).execute()
        print("   ✅ Connexion réussie à Supabase")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # 3. Vérifier les tables principales
    print("\n📊 Vérification des tables:")
    tables = [
        "utilisateurs",
        "candidats", 
        "recruteurs",
        "offres",
        "matchings",
        "candidatures"
    ]
    
    tables_ok = True
    for table in tables:
        try:
            supabase.table(table).select("*").limit(0).execute()
            print(f"   ✅ Table '{table}' existe")
        except Exception as e:
            print(f"   ❌ Table '{table}' MANQUANTE - Erreur: {str(e)[:50]}...")
            tables_ok = False
    
    # 4. Vérifier les types ENUM
    print("\n🔤 Vérification des types ENUM:")
    try:
        # Test indirect via une insertion test (sera rollback)
        result = supabase.rpc("version").execute()
        print("   ✅ Base de données accessible")
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier les ENUMs: {str(e)[:50]}...")
    
    # 5. Résumé
    print("\n" + "=" * 60)
    if tables_ok:
        print("✅ SUPABASE EST CORRECTEMENT CONFIGURÉ")
        print("\nVous pouvez:")
        print("   1. Lancer l'API: python run.py")
        print("   2. Accéder à la doc: http://localhost:8000/docs")
    else:
        print("❌ CONFIGURATION INCOMPLÈTE")
        print("\nActions requises:")
        print("   1. Aller sur: https://app.supabase.com/project/tlczregxeuyybtzsqdsj/sql/new")
        print("   2. Copier le contenu de: supabase/schema.sql")
        print("   3. Exécuter le script (bouton RUN)")
    print("=" * 60)
    
    return tables_ok

if __name__ == "__main__":
    try:
        check_supabase_connection()
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        print("\nVérifiez votre fichier .env")
        sys.exit(1)
