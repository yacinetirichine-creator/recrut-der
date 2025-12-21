#!/bin/bash

# 🎯 Recrut'der - Script de démarrage complet
# ============================================

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🎯 RECRUT'DER - Démarrage Automatique                      ║"
echo "║   Version 2.0.0 - Security Enhanced                          ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier si dans le bon répertoire
if [ ! -f "run.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

# Vérifier environnement virtuel
if [ ! -d ".venv" ]; then
    echo "❌ Erreur: Environnement virtuel .venv non trouvé"
    echo "   Créez-le avec: python3 -m venv .venv"
    exit 1
fi

# Activer l'environnement virtuel
echo "📦 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Vérifier les dépendances
echo "🔍 Vérification des dépendances..."
if ! python -c "import slowapi" 2>/dev/null; then
    echo "⚠️  Dépendance manquante détectée"
    echo "📥 Installation des dépendances..."
    pip install -r requirements.txt --quiet
    echo "✅ Dépendances installées"
else
    echo "✅ Dépendances OK"
fi

# Vérifier fichier .env
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env non trouvé"
    if [ -f ".env.example" ]; then
        echo "📝 Copie de .env.example vers .env..."
        cp .env.example .env
        echo "⚠️  IMPORTANT: Configurez vos variables dans .env avant de continuer"
        echo "   Appuyez sur Entrée quand c'est fait..."
        read
    else
        echo "❌ Erreur: .env.example non trouvé"
        exit 1
    fi
else
    echo "✅ Fichier .env trouvé"
fi

# Tests de sécurité
echo ""
echo "🧪 Exécution des tests de sécurité..."
python scripts/test_security.py
if [ $? -ne 0 ]; then
    echo "❌ Tests de sécurité échoués"
    echo "   Voulez-vous continuer quand même? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Tuer les processus existants sur les ports
echo ""
echo "🧹 Nettoyage des ports..."
lsof -ti:8000 | xargs kill 2>/dev/null && echo "   Port 8000 libéré"
lsof -ti:8001 | xargs kill 2>/dev/null && echo "   Port 8001 libéré"

# Créer les logs si nécessaire
mkdir -p logs

# Fonction pour gérer les signaux
cleanup() {
    echo ""
    echo "🛑 Arrêt des serveurs..."
    kill $API_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    echo "✅ Serveurs arrêtés"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Démarrer l'API
echo ""
echo "🚀 Démarrage de l'API..."
python run.py > logs/api.log 2>&1 &
API_PID=$!
sleep 3

# Vérifier que l'API a démarré
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'API n'a pas démarré correctement"
    echo "   Vérifiez les logs: tail -f logs/api.log"
    kill $API_PID 2>/dev/null
    exit 1
fi
echo "✅ API démarrée (PID: $API_PID)"

# Démarrer le site web
echo ""
echo "🌐 Démarrage du site web..."
cd website
python3 -m http.server 8001 > ../logs/web.log 2>&1 &
WEB_PID=$!
cd ..
sleep 2

# Vérifier que le site web a démarré
if ! curl -s http://localhost:8001 > /dev/null; then
    echo "❌ Le site web n'a pas démarré correctement"
    kill $API_PID $WEB_PID 2>/dev/null
    exit 1
fi
echo "✅ Site web démarré (PID: $WEB_PID)"

# Afficher les informations
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ✅ Recrut'der est maintenant en cours d'exécution !        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📡 API (Backend)"
echo "   → http://localhost:8000"
echo "   → Swagger: http://localhost:8000/docs"
echo "   → Health: http://localhost:8000/health"
echo ""
echo "🌐 Site Web (Frontend)"
echo "   → http://localhost:8001/index.html"
echo "   → App: http://localhost:8001/app.html"
echo ""
echo "🤖 Chatbot IA"
echo "   → Disponible sur toutes les pages"
echo "   → Bouton flottant en bas à droite"
echo "   → 10 langues supportées"
echo ""
echo "📊 Logs"
echo "   → API: tail -f logs/api.log"
echo "   → Web: tail -f logs/web.log"
echo ""
echo "🛑 Pour arrêter: Appuyez sur Ctrl+C"
echo ""

# Ouvrir le navigateur (optionnel)
if command -v open &> /dev/null; then
    echo "🌐 Ouverture du navigateur..."
    sleep 1
    open http://localhost:8001/index.html
elif command -v xdg-open &> /dev/null; then
    echo "🌐 Ouverture du navigateur..."
    sleep 1
    xdg-open http://localhost:8001/index.html
fi

# Attendre
echo "⏳ En attente... (Ctrl+C pour arrêter)"
wait
