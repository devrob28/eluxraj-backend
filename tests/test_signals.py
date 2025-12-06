import pytest

class TestSignals:
    def test_get_signals_authenticated(self, client, auth_headers):
        response = client.get("/api/v1/signals/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data
        assert "page" in data
    
    def test_get_signals_unauthenticated(self, client):
        response = client.get("/api/v1/signals/")
        assert response.status_code == 403
    
    def test_get_signals_with_filters(self, client, auth_headers):
        response = client.get(
            "/api/v1/signals/?min_score=70&symbol=BTC",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_performance_summary(self, client, auth_headers):
        response = client.get(
            "/api/v1/signals/performance/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "total_signals" in data
        assert "win_rate" in data
