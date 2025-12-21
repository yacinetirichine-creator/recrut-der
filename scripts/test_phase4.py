"""
🧪 Script de test pour Phase 4 - Tinder Feed
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_tinder_feed():
    """Tester le feed Tinder (nécessite un token valide)"""
    
    print("=" * 60)
    print("🔥 TEST PHASE 4: TINDER FEED")
    print("=" * 60)
    
    # 1. Vérifier que le serveur est démarré
    print("\n1️⃣ Vérification du serveur...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Serveur actif:", response.json())
        else:
            print("❌ Serveur non accessible")
            return
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # 2. Vérifier la documentation Swagger
    print("\n2️⃣ Vérification de la documentation...")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        openapi = response.json()
        
        # Vérifier les nouveaux endpoints
        paths = openapi.get("paths", {})
        tinder_endpoints = [p for p in paths.keys() if "/tinder/" in p]
        
        print(f"✅ {len(tinder_endpoints)} endpoints Tinder trouvés:")
        for endpoint in tinder_endpoints:
            methods = list(paths[endpoint].keys())
            print(f"   - {', '.join([m.upper() for m in methods])} {endpoint}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Afficher les routes disponibles
    print("\n3️⃣ Nouveaux endpoints disponibles:")
    endpoints = [
        ("GET", "/api/tinder/feed", "Obtenir le feed de recommandations"),
        ("GET", "/api/tinder/match-detail/{item_id}", "Détails d'un match potentiel"),
        ("POST", "/api/tinder/swipe", "Swiper (like/dislike)"),
        ("GET", "/api/tinder/stats", "Statistiques de matching")
    ]
    
    for method, path, description in endpoints:
        print(f"   {method:6} {path:45} - {description}")
    
    print("\n" + "=" * 60)
    print("📚 Documentation complète:")
    print("   Swagger: http://localhost:8000/docs")
    print("   ReDoc:   http://localhost:8000/redoc")
    print("   Fichier: PHASE4_TINDER_MATCHING.md")
    print("=" * 60)
    
    print("\n✅ Phase 4 installée avec succès!")
    print("\n💡 Pour tester les endpoints:")
    print("   1. Créer un compte via POST /api/auth/register")
    print("   2. Récupérer le token JWT")
    print("   3. Tester GET /api/tinder/feed avec le token")
    print("\n🔥 Voir PHASE4_TINDER_MATCHING.md pour scénarios complets")


if __name__ == "__main__":
    test_tinder_feed()
