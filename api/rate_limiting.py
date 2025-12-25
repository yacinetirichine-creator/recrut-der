"""
⏱️ Rate Limiting Utilities
===========================
Outils pour gérer le rate limiting sur les endpoints sensibles
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Instance globale du limiter
limiter = Limiter(key_func=get_remote_address)

# Configuration des limites par endpoint
RATE_LIMITS = {
    "auth:login": "5/minute",      # 5 tentatives/minute pour login
    "auth:register": "3/minute",    # 3 inscriptions/minute
    "auth:reset_password": "3/hour", # 3 demandes/heure
    "support:chat": "50/minute",    # 50 messages/minute
    "support:ticket": "10/minute",  # 10 tickets/minute
}

# Fonctions helper pour les limites courantes
def limit_login():
    return limiter.limit("5/minute")

def limit_register():
    return limiter.limit("3/minute")

def limit_password_reset():
    return limiter.limit("3/hour")

def limit_chat():
    return limiter.limit("50/minute")

def limit_ticket():
    return limiter.limit("10/minute")
