"""
🧠 Recrut'der - Moteur de Matching IA
=====================================
Algorithme de scoring multi-critères
"""

from typing import Dict, List


class MatchingEngine:
    """Moteur de matching intelligent entre candidats et offres."""
    
    POIDS = {
        "competences_techniques": 25,
        "experience": 25,
        "qualifications": 25,
        "salaire": 8,
        "localisation": 7,
        "secteur": 2,
        "type_contrat": 2,
        "disponibilite": 1,
        "langues": 2,
        "soft_skills": 1,
        "taille_entreprise": 1,
        "teletravail": 1,
    }
    
    @staticmethod
    def normaliser(texte: str) -> str:
        return texte.lower().strip()
    
    @classmethod
    def score_competences_techniques(cls, candidat: Dict, offre: Dict) -> Dict:
        competences_candidat = set([cls.normaliser(c) for c in candidat.get("competences_techniques", [])])
        requises = set([cls.normaliser(c) for c in offre.get("competences_requises", [])])
        bonus = set([cls.normaliser(c) for c in offre.get("competences_bonus", [])])
        
        requises_trouvees = competences_candidat.intersection(requises)
        bonus_trouvees = competences_candidat.intersection(bonus)
        
        if len(requises) == 0:
            score_requis = 100
        else:
            score_requis = (len(requises_trouvees) / len(requises)) * 100
        
        score_bonus = min(20, (len(bonus_trouvees) / len(bonus)) * 20) if len(bonus) > 0 else 0
        score_final = min(100, score_requis * 0.8 + score_bonus)
        
        return {
            "score": round(score_final, 1),
            "detail": f"{len(requises_trouvees)}/{len(requises)} requises, {len(bonus_trouvees)}/{len(bonus)} bonus",
            "requises_manquantes": list(requises - requises_trouvees),
            "bonus_trouvees": list(bonus_trouvees)
        }
    
    @classmethod
    def score_experience(cls, candidat: Dict, offre: Dict) -> Dict:
        exp = candidat.get("experience_annees", 0)
        exp_min = offre.get("experience_min", 0)
        exp_max = offre.get("experience_max", 50)
        
        if exp_min <= exp <= exp_max:
            score = 100
            detail = f"{exp} ans ✓ (demandé: {exp_min}-{exp_max})"
        elif exp < exp_min:
            ecart = exp_min - exp
            score = max(0, 100 - (ecart * 30) - (ecart - 1) * 10)
            detail = f"{exp} ans < {exp_min} minimum (-{ecart} an(s))"
        else:
            ecart = exp - exp_max
            score = max(60, 100 - (ecart * 8))
            detail = f"{exp} ans > {exp_max} max (surqualifié +{ecart} an(s))"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_qualifications(cls, candidat: Dict, offre: Dict) -> Dict:
        qualifs_candidat = [cls.normaliser(q) for q in candidat.get("qualifications", [])]
        requises = [cls.normaliser(q) for q in offre.get("qualifications_requises", [])]
        bonus = [cls.normaliser(q) for q in offre.get("qualifications_bonus", [])]
        
        def match_qualification(candidat_quals, recherchees):
            trouvees = []
            for recherchee in recherchees:
                for qual_cand in candidat_quals:
                    mots_recherche = set(recherchee.split())
                    mots_candidat = set(qual_cand.split())
                    if (recherchee in qual_cand or qual_cand in recherchee or 
                        len(mots_recherche.intersection(mots_candidat)) >= 1):
                        trouvees.append(recherchee)
                        break
            return trouvees
        
        if len(requises) == 0:
            score_requis = 100
            requises_trouvees = []
        else:
            requises_trouvees = match_qualification(qualifs_candidat, requises)
            score_requis = (len(requises_trouvees) / len(requises)) * 100
        
        bonus_trouvees = match_qualification(qualifs_candidat, bonus)
        score_bonus = min(20, len(bonus_trouvees) * 10)
        score_final = min(100, score_requis * 0.8 + score_bonus)
        
        return {"score": round(score_final, 1), "detail": f"{len(requises_trouvees)}/{len(requises)} requises, {len(bonus_trouvees)}/{len(bonus)} bonus"}
    
    @classmethod
    def score_salaire(cls, candidat: Dict, offre: Dict) -> Dict:
        cand_min = candidat.get("salaire_min", 0)
        cand_max = candidat.get("salaire_max", 0)
        offre_min = offre.get("salaire_min", 0)
        offre_max = offre.get("salaire_max", 0)
        
        overlap_min = max(cand_min, offre_min)
        overlap_max = min(cand_max, offre_max)
        
        if overlap_min <= overlap_max:
            overlap = overlap_max - overlap_min
            total_range = max(cand_max, offre_max) - min(cand_min, offre_min)
            score = min(100, 60 + (overlap / total_range) * 40) if total_range > 0 else 100
            detail = f"Zone commune: {overlap_min//1000}-{overlap_max//1000}k€"
        else:
            if cand_min > offre_max:
                ecart = cand_min - offre_max
                detail = f"Candidat +{ecart//1000}k€ au-dessus"
            else:
                ecart = offre_min - cand_max
                detail = f"Offre +{ecart//1000}k€ au-dessus"
            score = max(15, 50 - (ecart / 1000) * 5)
        
        return {"score": round(score, 1), "detail": f"Candidat: {cand_min//1000}-{cand_max//1000}k€ | Offre: {offre_min//1000}-{offre_max//1000}k€ → {detail}"}
    
    @classmethod
    def score_localisation(cls, candidat: Dict, offre: Dict) -> Dict:
        meme_ville = cls.normaliser(candidat.get("localisation", "")) == cls.normaliser(offre.get("localisation", ""))
        candidat_remote = candidat.get("accept_remote", False)
        offre_remote = offre.get("remote_possible", False)
        
        if meme_ville:
            score, detail = 100, f"Même ville : {candidat.get('localisation', '').title()} ✓"
        elif candidat_remote and offre_remote:
            score, detail = 95, "Remote OK des 2 côtés"
        elif offre_remote and not candidat_remote:
            score, detail = 85, "Remote proposé, candidat préfère présentiel"
        elif candidat_remote and not offre_remote:
            score, detail = 35, "Candidat OK remote, offre présentiel uniquement"
        else:
            score, detail = 15, "Villes différentes, pas de remote"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_secteur(cls, candidat: Dict, offre: Dict) -> Dict:
        secteurs_candidat = [cls.normaliser(s) for s in candidat.get("secteurs", [])]
        secteur_offre = cls.normaliser(offre.get("secteur", ""))
        
        if secteur_offre in secteurs_candidat:
            score, detail = 100, f"Secteur '{offre.get('secteur', '')}' ✓"
        else:
            score, detail = 40, f"Secteur '{offre.get('secteur', '')}' pas dans préférences"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_type_contrat(cls, candidat: Dict, offre: Dict) -> Dict:
        contrats_candidat = [cls.normaliser(c) for c in candidat.get("type_contrat_souhaite", [])]
        contrat_offre = cls.normaliser(offre.get("type_contrat", "cdi"))
        
        if contrat_offre in contrats_candidat:
            score, detail = 100, f"{offre.get('type_contrat', 'CDI').upper()} ✓"
        elif "cdi" in contrats_candidat and contrat_offre == "cdd":
            score, detail = 60, "CDD proposé, CDI préféré"
        else:
            score, detail = 30, f"{offre.get('type_contrat', '').upper()} ne correspond pas"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_disponibilite(cls, candidat: Dict, offre: Dict) -> Dict:
        dispo_candidat = cls.normaliser(candidat.get("disponibilite", "1_mois"))
        dispo_offre = cls.normaliser(offre.get("date_debut_souhaitee", "flexible"))
        
        ordre = {"immediate": 0, "1_mois": 1, "3_mois": 2, "flexible": 3}
        
        if dispo_offre == "flexible":
            score, detail = 100, "Entreprise flexible sur la date"
        elif dispo_candidat == dispo_offre:
            score, detail = 100, "Disponibilité alignée"
        elif ordre.get(dispo_candidat, 2) <= ordre.get(dispo_offre, 2):
            score, detail = 90, "Candidat dispo avant la date souhaitée"
        else:
            ecart = ordre.get(dispo_candidat, 2) - ordre.get(dispo_offre, 2)
            score = max(40, 100 - ecart * 25)
            detail = "Candidat dispo plus tard que souhaité"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_langues(cls, candidat: Dict, offre: Dict) -> Dict:
        langues_candidat = set([cls.normaliser(l) for l in candidat.get("langues", [])])
        requises = set([cls.normaliser(l) for l in offre.get("langues_requises", [])])
        bonus = set([cls.normaliser(l) for l in offre.get("langues_bonus", [])])
        
        if len(requises) == 0:
            return {"score": 100, "detail": "Pas de langue requise"}
        
        requises_trouvees = langues_candidat.intersection(requises)
        if len(requises_trouvees) == len(requises):
            bonus_trouvees = langues_candidat.intersection(bonus)
            score = min(100, 85 + len(bonus_trouvees) * 5)
            detail = f"Toutes les langues requises ✓" + (f" + {len(bonus_trouvees)} bonus" if bonus_trouvees else "")
        else:
            score = (len(requises_trouvees) / len(requises)) * 70
            manquantes = requises - requises_trouvees
            detail = f"Manque: {', '.join(manquantes)}"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_soft_skills(cls, candidat: Dict, offre: Dict) -> Dict:
        skills_candidat = set([cls.normaliser(s) for s in candidat.get("soft_skills", [])])
        skills_recherches = set([cls.normaliser(s) for s in offre.get("soft_skills_recherches", [])])
        
        if len(skills_recherches) == 0:
            return {"score": 100, "detail": "Pas de soft skills spécifiés"}
        
        trouvees = skills_candidat.intersection(skills_recherches)
        score = (len(trouvees) / len(skills_recherches)) * 100
        
        return {"score": round(score, 1), "detail": f"{len(trouvees)}/{len(skills_recherches)} soft skills matchés"}
    
    @classmethod
    def score_taille_entreprise(cls, candidat: Dict, offre: Dict) -> Dict:
        prefs = [cls.normaliser(t) for t in candidat.get("taille_entreprise_preferee", [])]
        taille_offre = cls.normaliser(offre.get("taille_entreprise", ""))
        
        if not prefs or not taille_offre:
            return {"score": 80, "detail": "Non spécifié"}
        
        if taille_offre in prefs:
            score, detail = 100, f"{offre.get('taille_entreprise', '').replace('_', ' ').title()} ✓"
        else:
            score, detail = 50, f"Préfère: {', '.join(prefs)}"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def score_teletravail(cls, candidat: Dict, offre: Dict) -> Dict:
        pref_candidat = cls.normaliser(candidat.get("preference_teletravail", "hybride"))
        politique_offre = cls.normaliser(offre.get("politique_teletravail", "hybride"))
        
        if pref_candidat == politique_offre:
            score, detail = 100, f"Politique {politique_offre} alignée ✓"
        elif pref_candidat == "hybride" or politique_offre == "hybride":
            score, detail = 85, "Hybride compatible"
        elif pref_candidat == "full_remote" and politique_offre == "presentiel":
            score, detail = 30, "Candidat veut full remote, offre présentiel"
        elif pref_candidat == "presentiel" and politique_offre == "full_remote":
            score, detail = 60, "Candidat préfère présentiel, offre full remote"
        else:
            score, detail = 70, "Légère différence de préférence"
        
        return {"score": round(score, 1), "detail": detail}
    
    @classmethod
    def calculer_matching(cls, candidat: Dict, offre: Dict) -> Dict:
        scores = {
            "competences_techniques": cls.score_competences_techniques(candidat, offre),
            "experience": cls.score_experience(candidat, offre),
            "qualifications": cls.score_qualifications(candidat, offre),
            "salaire": cls.score_salaire(candidat, offre),
            "localisation": cls.score_localisation(candidat, offre),
            "secteur": cls.score_secteur(candidat, offre),
            "type_contrat": cls.score_type_contrat(candidat, offre),
            "disponibilite": cls.score_disponibilite(candidat, offre),
            "langues": cls.score_langues(candidat, offre),
            "soft_skills": cls.score_soft_skills(candidat, offre),
            "taille_entreprise": cls.score_taille_entreprise(candidat, offre),
            "teletravail": cls.score_teletravail(candidat, offre),
        }
        
        score_global = sum(scores[critere]["score"] * (poids / 100) for critere, poids in cls.POIDS.items())
        
        points_forts = [k for k, v in scores.items() if v["score"] >= 80]
        points_faibles = [k for k, v in scores.items() if v["score"] < 50]
        
        if score_global >= 85:
            recommandation = "🟢 EXCELLENT MATCH - Profil idéal, à contacter en priorité !"
            emoji, niveau = "💚", "excellent"
        elif score_global >= 70:
            recommandation = "🟡 TRÈS BON MATCH - Profil solide à considérer"
            emoji, niveau = "💛", "tres_bon"
        elif score_global >= 55:
            recommandation = "🟠 MATCH CORRECT - Quelques écarts à discuter"
            emoji, niveau = "🧡", "correct"
        elif score_global >= 40:
            recommandation = "🔴 MATCH FAIBLE - Profil peu adapté"
            emoji, niveau = "❤️", "faible"
        else:
            recommandation = "⚫ PAS DE MATCH - Profil non compatible"
            emoji, niveau = "🖤", "incompatible"
        
        return {
            "candidat_id": candidat.get("id"),
            "offre_id": offre.get("id"),
            "candidat_nom": candidat.get("nom", ""),
            "offre_titre": offre.get("titre", ""),
            "entreprise": offre.get("entreprise", ""),
            "score_global": round(score_global, 1),
            "niveau": niveau,
            "emoji": emoji,
            "recommandation": recommandation,
            "scores_details": scores,
            "points_forts": points_forts,
            "points_faibles": points_faibles
        }
    
    @classmethod
    def top_offres_pour_candidat(cls, candidat: Dict, offres: List[Dict], top_n: int = 5) -> List[Dict]:
        resultats = [cls.calculer_matching(candidat, offre) for offre in offres]
        resultats.sort(key=lambda x: x["score_global"], reverse=True)
        return resultats[:top_n]
    
    @classmethod
    def top_candidats_pour_offre(cls, offre: Dict, candidats: List[Dict], top_n: int = 5) -> List[Dict]:
        resultats = [cls.calculer_matching(candidat, offre) for candidat in candidats]
        resultats.sort(key=lambda x: x["score_global"], reverse=True)
        return resultats[:top_n]
    
    @classmethod
    def matrice_complete(cls, candidats: List[Dict], offres: List[Dict]) -> Dict:
        matchings = []
        tous_scores = []
        niveaux = {"excellent": 0, "tres_bon": 0, "correct": 0, "faible": 0, "incompatible": 0}
        
        for candidat in candidats:
            for offre in offres:
                resultat = cls.calculer_matching(candidat, offre)
                matchings.append({
                    "candidat_id": candidat["id"],
                    "candidat_nom": candidat["nom"],
                    "offre_id": offre["id"],
                    "offre_titre": offre["titre"],
                    "score": resultat["score_global"],
                    "niveau": resultat["niveau"],
                    "emoji": resultat["emoji"]
                })
                tous_scores.append(resultat["score_global"])
                niveaux[resultat["niveau"]] += 1
        
        return {
            "total_candidats": len(candidats),
            "total_offres": len(offres),
            "total_matchings": len(matchings),
            "matchings": matchings,
            "statistiques": {
                "score_moyen": round(sum(tous_scores) / len(tous_scores), 1) if tous_scores else 0,
                "score_min": min(tous_scores) if tous_scores else 0,
                "score_max": max(tous_scores) if tous_scores else 0,
                "repartition": niveaux
            }
        }
