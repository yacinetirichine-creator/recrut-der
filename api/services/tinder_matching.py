"""
🎯 Recrut'der - Moteur de Matching IA Avancé (Type Tinder)
===========================================================
Algorithme intelligent avec scoring personnalisé et feed de recommandations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import random


class TinderMatchingEngine:
    """
    Moteur de matching type Tinder avec algorithme intelligent.
    
    Features:
    - Scoring multi-critères personnalisé
    - Feed de recommandations intelligent
    - Apprentissage des préférences utilisateur
    - Boost de visibilité
    - Fraîcheur des profils
    """
    
    # Poids par défaut (peuvent être ajustés par préférences utilisateur)
    DEFAULT_WEIGHTS = {
        "competences_techniques": 25,
        "experience": 20,
        "qualifications": 20,
        "salaire": 10,
        "localisation": 10,
        "secteur": 5,
        "type_contrat": 3,
        "langues": 3,
        "soft_skills": 2,
        "taille_entreprise": 2,
    }
    
    
    @classmethod
    def calculate_smart_score(
        cls,
        candidat: Dict,
        offre: Dict,
        user_preferences: Optional[Dict] = None,
        swipe_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculer un score intelligent entre candidat et offre.
        
        Args:
            candidat: Profil candidat
            offre: Offre d'emploi
            user_preferences: Préférences utilisateur (poids personnalisés)
            swipe_history: Historique des swipes pour ajuster l'algo
            
        Returns:
            Dict avec score global, détails, et explications
        """
        # Utiliser les poids personnalisés ou par défaut
        weights = user_preferences.get("weights", cls.DEFAULT_WEIGHTS) if user_preferences else cls.DEFAULT_WEIGHTS
        
        # Calculer chaque score
        scores = {
            "competences": cls._score_competences(candidat, offre),
            "experience": cls._score_experience(candidat, offre),
            "qualifications": cls._score_qualifications(candidat, offre),
            "salaire": cls._score_salaire(candidat, offre),
            "localisation": cls._score_localisation(candidat, offre),
            "secteur": cls._score_secteur(candidat, offre),
            "type_contrat": cls._score_type_contrat(candidat, offre),
            "langues": cls._score_langues(candidat, offre),
            "soft_skills": cls._score_soft_skills(candidat, offre),
            "taille_entreprise": cls._score_taille_entreprise(candidat, offre),
        }
        
        # Calculer le score global pondéré
        score_global = 0
        total_weight = 0
        
        for key, weight in weights.items():
            if key in scores:
                score_global += scores[key]["score"] * (weight / 100)
                total_weight += weight
        
        # Normaliser sur 100
        if total_weight > 0:
            score_global = (score_global / total_weight) * 100
        
        # Ajuster avec l'historique des swipes (machine learning simple)
        if swipe_history:
            adjustment = cls._calculate_preference_adjustment(candidat, offre, swipe_history)
            score_global = min(100, score_global + adjustment)
        
        # Bonus fraîcheur (nouveaux profils/offres)
        freshness_bonus = cls._calculate_freshness_bonus(offre)
        score_global = min(100, score_global + freshness_bonus)
        
        return {
            "score_global": round(score_global, 1),
            "scores_detailles": scores,
            "niveau_match": cls._get_match_level(score_global),
            "explication": cls._generate_explanation(scores, score_global),
            "points_forts": cls._extract_strengths(scores),
            "points_amelioration": cls._extract_weaknesses(scores),
        }
    
    
    @classmethod
    def get_recommendation_feed(
        cls,
        user_id: str,
        user_type: str,  # 'candidat' or 'recruteur'
        user_profile: Dict,
        all_candidates: List[Dict] = None,
        all_offers: List[Dict] = None,
        already_swiped: List[str] = None,
        swipe_history: List[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Générer un feed de recommandations intelligent type Tinder.
        
        Args:
            user_id: ID de l'utilisateur
            user_type: 'candidat' ou 'recruteur'
            user_profile: Profil de l'utilisateur
            all_candidates: Liste de tous les candidats (si recruteur)
            all_offers: Liste de toutes les offres (si candidat)
            already_swiped: Liste des IDs déjà swipés
            swipe_history: Historique complet des swipes
            limit: Nombre de recommandations
            
        Returns:
            Liste de profils/offres recommandés avec scores
        """
        already_swiped = already_swiped or []
        
        # Filtrer les éléments déjà swipés
        if user_type == "candidat":
            items = [o for o in (all_offers or []) if o["id"] not in already_swiped]
            is_candidat = True
        else:
            items = [c for c in (all_candidates or []) if c["id"] not in already_swiped]
            is_candidat = False
        
        # Calculer le score pour chaque item
        scored_items = []
        for item in items:
            if is_candidat:
                score_data = cls.calculate_smart_score(
                    candidat=user_profile,
                    offre=item,
                    swipe_history=swipe_history
                )
            else:
                score_data = cls.calculate_smart_score(
                    candidat=item,
                    offre=user_profile,
                    swipe_history=swipe_history
                )
            
            scored_items.append({
                **item,
                "match_score": score_data["score_global"],
                "match_data": score_data
            })
        
        # Trier par score décroissant
        scored_items.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Algorithme de diversification (ne pas montrer QUE les meilleurs)
        # 70% top matches, 20% bons matches, 10% découverte
        top_count = int(limit * 0.7)
        good_count = int(limit * 0.2)
        discovery_count = limit - top_count - good_count
        
        recommendations = []
        
        # Top matches
        if len(scored_items) > 0:
            recommendations.extend(scored_items[:top_count])
        
        # Bons matches (pas les meilleurs mais solides)
        if len(scored_items) > top_count:
            good_matches = scored_items[top_count:top_count + good_count + 20]
            recommendations.extend(random.sample(good_matches, min(good_count, len(good_matches))))
        
        # Découverte (aléatoire pour diversifier)
        if len(scored_items) > top_count + good_count:
            discovery_pool = scored_items[top_count + good_count:]
            recommendations.extend(random.sample(discovery_pool, min(discovery_count, len(discovery_pool))))
        
        # Mélanger légèrement pour éviter la prédictibilité
        random.shuffle(recommendations)
        
        return recommendations[:limit]
    
    
    @classmethod
    def _score_competences(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score des compétences techniques"""
        comp_candidat = set([c.lower().strip() for c in candidat.get("competences_techniques", [])])
        requises = set([c.lower().strip() for c in offre.get("competences_requises", [])])
        bonus = set([c.lower().strip() for c in offre.get("competences_bonus", [])])
        
        if not requises:
            return {"score": 80, "detail": "Aucune compétence requise spécifiée"}
        
        requises_ok = comp_candidat.intersection(requises)
        bonus_ok = comp_candidat.intersection(bonus)
        
        score = (len(requises_ok) / len(requises)) * 100
        if bonus_ok:
            score = min(100, score + len(bonus_ok) * 5)
        
        return {
            "score": round(score, 1),
            "detail": f"{len(requises_ok)}/{len(requises)} requises",
            "manquantes": list(requises - requises_ok),
            "bonus": list(bonus_ok)
        }
    
    
    @classmethod
    def _score_experience(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score de l'expérience"""
        exp = candidat.get("experience_annees", 0)
        exp_min = offre.get("experience_min", 0)
        exp_max = offre.get("experience_max", 50)
        
        if exp_min <= exp <= exp_max:
            score = 100
        elif exp < exp_min:
            ecart = exp_min - exp
            score = max(0, 100 - (ecart * 25))
        else:
            score = 85  # Surqualifié mais OK
        
        return {
            "score": round(score, 1),
            "detail": f"{exp} ans (demandé: {exp_min}-{exp_max})"
        }
    
    
    @classmethod
    def _score_qualifications(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score des qualifications/diplômes"""
        quals_cand = candidat.get("qualifications", [])
        quals_req = offre.get("qualifications_requises", [])
        
        if not quals_req:
            return {"score": 80, "detail": "Aucune qualification requise"}
        
        # Match simple sur les mots-clés
        matches = sum(1 for qr in quals_req if any(qr.lower() in qc.lower() for qc in quals_cand))
        score = (matches / len(quals_req)) * 100
        
        return {
            "score": round(score, 1),
            "detail": f"{matches}/{len(quals_req)} qualifications"
        }
    
    
    @classmethod
    def _score_salaire(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score de compatibilité salariale"""
        cand_min = candidat.get("salaire_min", 0)
        cand_max = candidat.get("salaire_max", 999999)
        offre_min = offre.get("salaire_min", 0)
        offre_max = offre.get("salaire_max", 999999)
        
        # Zone de chevauchement
        overlap_min = max(cand_min, offre_min)
        overlap_max = min(cand_max, offre_max)
        
        if overlap_min <= overlap_max:
            score = 100
            detail = "Fourchettes compatibles"
        else:
            ecart = abs(cand_min - offre_max)
            score = max(30, 100 - (ecart / 5000))
            detail = f"Écart de {ecart//1000}k€"
        
        return {"score": round(score, 1), "detail": detail}
    
    
    @classmethod
    def _score_localisation(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score de localisation"""
        same_city = candidat.get("localisation", "").lower() == offre.get("localisation", "").lower()
        remote_ok_cand = candidat.get("accept_remote", False)
        remote_ok_offre = offre.get("remote_possible", False)
        
        if same_city:
            return {"score": 100, "detail": "Même ville"}
        elif remote_ok_cand and remote_ok_offre:
            return {"score": 95, "detail": "Remote OK"}
        elif remote_ok_offre:
            return {"score": 70, "detail": "Remote possible"}
        else:
            return {"score": 30, "detail": "Villes différentes"}
    
    
    @classmethod
    def _score_secteur(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score du secteur d'activité"""
        secteurs_cand = [s.lower() for s in candidat.get("secteurs", [])]
        secteur_offre = offre.get("secteur", "").lower()
        
        if not secteurs_cand or not secteur_offre:
            return {"score": 50, "detail": "Secteur non spécifié"}
        
        score = 100 if secteur_offre in secteurs_cand else 40
        return {"score": score, "detail": "Match secteur" if score == 100 else "Secteur différent"}
    
    
    @classmethod
    def _score_type_contrat(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score du type de contrat"""
        contrats_cand = [c.lower() for c in candidat.get("type_contrat_souhaite", ["cdi"])]
        contrat_offre = offre.get("type_contrat", "cdi").lower()
        
        score = 100 if contrat_offre in contrats_cand else 50
        return {"score": score, "detail": f"{contrat_offre}"}
    
    
    @classmethod
    def _score_langues(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score des langues"""
        langues_cand = set([l.lower() for l in candidat.get("langues", ["français"])])
        langues_req = set([l.lower() for l in offre.get("langues_requises", ["français"])])
        
        if not langues_req:
            return {"score": 80, "detail": "Aucune langue requise"}
        
        matches = langues_cand.intersection(langues_req)
        score = (len(matches) / len(langues_req)) * 100
        
        return {"score": round(score, 1), "detail": f"{len(matches)}/{len(langues_req)} langues"}
    
    
    @classmethod
    def _score_soft_skills(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score des soft skills"""
        soft_cand = set([s.lower() for s in candidat.get("soft_skills", [])])
        soft_req = set([s.lower() for s in offre.get("soft_skills_recherches", [])])
        
        if not soft_req:
            return {"score": 70, "detail": "Aucun soft skill spécifié"}
        
        matches = soft_cand.intersection(soft_req)
        score = (len(matches) / len(soft_req)) * 100 if soft_req else 70
        
        return {"score": round(score, 1), "detail": f"{len(matches)} soft skills communs"}
    
    
    @classmethod
    def _score_taille_entreprise(cls, candidat: Dict, offre: Dict) -> Dict:
        """Score de la taille d'entreprise"""
        pref_cand = [t.lower() for t in candidat.get("taille_entreprise_preferee", [])]
        taille_offre = offre.get("taille_entreprise", "").lower()
        
        if not pref_cand or not taille_offre:
            return {"score": 60, "detail": "Pas de préférence"}
        
        score = 100 if taille_offre in pref_cand else 50
        return {"score": score, "detail": taille_offre}
    
    
    @classmethod
    def _calculate_preference_adjustment(cls, candidat: Dict, offre: Dict, swipe_history: List[Dict]) -> float:
        """
        Ajuster le score en fonction des préférences apprises.
        Machine learning simple basé sur l'historique.
        """
        if not swipe_history or len(swipe_history) < 5:
            return 0
        
        # Analyser les likes vs dislikes
        likes = [s for s in swipe_history if s.get("action") == "like"]
        
        if not likes:
            return 0
        
        # Patterns simples (peut être amélioré avec vraie ML)
        adjustment = 0
        
        # Exemple: si l'user like souvent les startups
        if any("startup" in str(s).lower() for s in likes[-5:]):
            if offre.get("taille_entreprise", "").lower() == "startup":
                adjustment += 5
        
        return min(10, adjustment)
    
    
    @classmethod
    def _calculate_freshness_bonus(cls, offre: Dict) -> float:
        """Bonus pour les nouvelles offres (encourage la découverte)"""
        created_at = offre.get("created_at")
        if not created_at:
            return 0
        
        # Offres de moins de 7 jours = +3 points
        # TODO: parser la date correctement
        return 2  # Bonus fixe pour l'instant
    
    
    @classmethod
    def _get_match_level(cls, score: float) -> str:
        """Niveau de match en fonction du score"""
        if score >= 85:
            return "🔥 Excellent Match"
        elif score >= 70:
            return "✨ Très bon match"
        elif score >= 55:
            return "👍 Bon match"
        elif score >= 40:
            return "🤔 Match moyen"
        else:
            return "❌ Faible match"
    
    
    @classmethod
    def _generate_explanation(cls, scores: Dict, score_global: float) -> str:
        """Générer une explication du match"""
        top_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)[:3]
        
        explanations = [f"{key}: {data['score']:.0f}%" for key, data in top_scores]
        
        return f"Match basé principalement sur: {', '.join(explanations)}"
    
    
    @classmethod
    def _extract_strengths(cls, scores: Dict) -> List[str]:
        """Extraire les points forts du match"""
        return [
            key for key, data in scores.items()
            if data["score"] >= 80
        ]
    
    
    @classmethod
    def _extract_weaknesses(cls, scores: Dict) -> List[str]:
        """Extraire les points faibles du match"""
        return [
            key for key, data in scores.items()
            if data["score"] < 50
        ]
