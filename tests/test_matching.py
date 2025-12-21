"""
🧪 Tests Recrut'der
===================
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.matching_engine import MatchingEngine
from api.database.fake_data import candidats_db, offres_db

client = TestClient(app)


class TestAPI:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Recrut'der" in response.json()["message"]
    
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_lister_candidats(self):
        response = client.get("/api/candidats")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_lister_offres(self):
        response = client.get("/api/offres")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_matching_score(self):
        response = client.post("/api/matching/score", json={
            "candidat_id": 1,
            "offre_id": 101
        })
        assert response.status_code == 200
        assert "score_global" in response.json()


class TestMatchingEngine:
    def test_poids_100(self):
        assert sum(MatchingEngine.POIDS.values()) == 100
    
    def test_matching_sarah_data_analyst(self):
        candidat = candidats_db[1]
        offre = offres_db[101]
        result = MatchingEngine.calculer_matching(candidat, offre)
        assert result["score_global"] >= 85
        assert result["niveau"] == "excellent"
    
    def test_top_offres(self):
        candidat = candidats_db[4]
        offres = list(offres_db.values())
        resultats = MatchingEngine.top_offres_pour_candidat(candidat, offres, 3)
        assert len(resultats) == 3
        scores = [r["score_global"] for r in resultats]
        assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
