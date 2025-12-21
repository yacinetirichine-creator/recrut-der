"""Script pour vérifier la structure de support_tickets"""
import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# Vérifier la structure de la table
result = supabase.table("support_tickets").select("*").limit(0).execute()

print("✅ Table support_tickets existe")
print("\nEssai d'insertion pour voir les colonnes requises:")

try:
    # Essayer de créer un ticket minimal pour voir les erreurs
    test = supabase.table("support_tickets").insert({
        "user_email": "test@test.com",
        "sujet": "Test",
        "message": "Test message",
        "category": "technical",
        "priority": "medium",
        "status": "open"
    }).execute()
    print("✅ Structure attendue:", test)
except Exception as e:
    print(f"❌ Erreur (utile pour comprendre la structure): {e}")
