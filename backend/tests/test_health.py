"""Tests for health endpoint."""


def test_health_check(client):
    """Test health endpoint returns correct data."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "git_sha" in data
