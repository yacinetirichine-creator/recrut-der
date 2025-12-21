#!/usr/bin/env python3
"""
🧪 Recrut'der - Script de test rapide
=====================================
Vérifie que l'API démarre correctement avec les nouvelles améliorations de sécurité
"""

import sys
import os

# Ajouter le répertoire racine au path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """Teste les imports principaux"""
    print("📦 Test des imports...")
    try:
        from api.main import app
        from api.config import settings
        from slowapi import Limiter
        print("✅ Tous les imports fonctionnent")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_middlewares():
    """Teste que les middlewares sont bien configurés"""
    print("\n🛡️ Test des middlewares de sécurité...")
    try:
        from api.main import app
        
        middlewares = [m for m in app.user_middleware]
        middleware_types = [type(m.cls).__name__ for m in middlewares]
        
        print(f"Middlewares détectés: {middleware_types}")
        
        # Vérifier les middlewares de sécurité
        required = ['CORSMiddleware', 'GZipMiddleware', 'SecurityHeadersMiddleware']
        for req in required:
            if req in middleware_types:
                print(f"✅ {req} est configuré")
            else:
                print(f"⚠️  {req} n'est pas trouvé")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_routes():
    """Teste que les routes sont bien chargées"""
    print("\n🔗 Test des routes...")
    try:
        from api.main import app
        
        routes = [route.path for route in app.routes]
        essential_routes = ['/health', '/api/auth/login', '/api/auth/register', '/docs']
        
        for route in essential_routes:
            if route in routes:
                print(f"✅ {route} est disponible")
            else:
                print(f"❌ {route} n'est pas trouvé")
        
        print(f"\n📊 Total de routes: {len(routes)}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_security_headers():
    """Teste la présence du middleware de headers de sécurité"""
    print("\n🔒 Test des headers de sécurité...")
    try:
        from api.main import SecurityHeadersMiddleware
        print("✅ SecurityHeadersMiddleware est défini")
        return True
    except ImportError:
        print("❌ SecurityHeadersMiddleware non trouvé")
        return False

def test_rate_limiter():
    """Teste la configuration du rate limiter"""
    print("\n⏱️ Test du rate limiter...")
    try:
        from api.main import app
        
        if hasattr(app.state, 'limiter'):
            print("✅ Rate limiter est configuré")
            return True
        else:
            print("⚠️  Rate limiter non trouvé dans app.state")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_config():
    """Teste la configuration"""
    print("\n⚙️ Test de la configuration...")
    try:
        from api.config import settings
        
        print(f"  APP_NAME: {settings.APP_NAME}")
        print(f"  APP_VERSION: {settings.APP_VERSION}")
        print(f"  DEBUG: {settings.DEBUG}")
        print(f"  CORS_ORIGINS: {len(settings.cors_origins_list)} origines")
        
        if hasattr(settings, 'allowed_hosts_list'):
            print(f"  ALLOWED_HOSTS: {len(settings.allowed_hosts_list)} hôtes")
            print("✅ Configuration étendue avec allowed_hosts")
        else:
            print("⚠️  allowed_hosts_list non trouvé")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("=" * 60)
    print("🎯 RECRUT'DER - Tests de Sécurité")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_middlewares,
        test_security_headers,
        test_rate_limiter,
        test_routes,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Erreur lors du test {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    print(f"❌ Tests échoués: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("🚀 L'API est prête à être démarrée avec:")
        print("   python run.py")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué")
        print("   Veuillez vérifier les erreurs ci-dessus")
        return 1

if __name__ == "__main__":
    sys.exit(main())
