"""Integration tests for Health Check API"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.health import router


@pytest.fixture
def app():
    """Create a test FastAPI app with health routes"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/health")
    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


class TestHealthCheck:
    """Test basic health check endpoint"""

    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "pippulse-backend"

    def test_liveness_check(self, client):
        """Test liveness check"""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness check"""
        response = client.get("/health/ready")
        # Might fail due to no actual DB connections, but should be formatted correctly
        assert response.status_code in [200, 503]

    def test_websocket_metrics(self, client):
        """Test WebSocket metrics endpoint"""
        response = client.get("/health/websocket/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "websocket" in data
        assert "total_connections" in data["websocket"]
        assert "avg_latency_ms" in data["websocket"]

    def test_websocket_connections(self, client):
        """Test WebSocket connections endpoint"""
        response = client.get("/health/websocket/connections")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "active_connections" in data
        assert "max_connections" in data
        assert isinstance(data["active_connections"], int)
