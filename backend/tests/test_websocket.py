"""Integration tests for WebSocket API"""

import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.websocket import router, manager, ConnectionManager


@pytest.fixture
def app():
    """Create a test FastAPI app with WebSocket routes"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/ws")
    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
async def ws_manager():
    """Reset the connection manager before each test"""
    manager.active_connections.clear()
    manager.subscriptions.clear()
    manager.metrics.clear()
    yield manager
    manager.active_connections.clear()
    manager.subscriptions.clear()
    manager.metrics.clear()


class TestWebSocketBasics:
    """Test basic WebSocket functionality"""

    def test_websocket_connect(self, client):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws/") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "message" in data["data"]
            assert "timestamp" in data["data"]

    def test_websocket_ping_pong(self, client):
        """Test ping/pong heartbeat"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()

            assert response["type"] == "pong"
            assert "timestamp" in response["data"]

    def test_websocket_subscription(self, client):
        """Test subscription to message types"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({
                "type": "subscribe",
                "subscriptions": {
                    "signals": True,
                    "news": False
                }
            })
            response = websocket.receive_json()

            assert response["type"] == "subscribed"
            assert response["data"]["subscriptions"]["signals"] is True
            assert response["data"]["subscriptions"]["news"] is False

    def test_websocket_unsubscribe(self, client):
        """Test unsubscription from message types"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({
                "type": "subscribe",
                "subscriptions": {"signals": True}
            })
            websocket.receive_json()  # Subscribed confirmation

            websocket.send_json({
                "type": "unsubscribe",
                "message_type": "signals"
            })
            response = websocket.receive_json()

            assert response["type"] == "unsubscribed"
            assert response["data"]["message_type"] == "signals"

    def test_websocket_get_status(self, client):
        """Test getting connection status"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({"type": "get_status"})
            response = websocket.receive_json()

            assert response["type"] == "status"
            assert response["data"]["connected"] is True
            assert "connection_count" in response["data"]
            assert "subscriptions" in response["data"]
            assert "avg_latency_ms" in response["data"]

    def test_websocket_unknown_message(self, client):
        """Test handling unknown message type"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({"type": "unknown_type"})
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "Unknown message type" in response["data"]["message"]


class TestWebSocketSignals:
    """Test WebSocket signals endpoint"""

    def test_signals_websocket_connect(self, client):
        """Test connecting to signals endpoint"""
        with client.websocket_connect("/ws/signals") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_signals_heartbeat(self, client):
        """Test signals endpoint heartbeat"""
        with client.websocket_connect("/ws/signals") as websocket:
            websocket.receive_json()  # Connection message

            # Wait for heartbeat
            data = websocket.receive_json(timeout=35)
            assert data["type"] == "heartbeat"
            assert "timestamp" in data["data"]


class TestWebSocketNews:
    """Test WebSocket news endpoint"""

    def test_news_websocket_connect(self, client):
        """Test connecting to news endpoint"""
        with client.websocket_connect("/ws/news") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_news_heartbeat(self, client):
        """Test news endpoint heartbeat"""
        with client.websocket_connect("/ws/news") as websocket:
            websocket.receive_json()  # Connection message

            # Wait for heartbeat
            data = websocket.receive_json(timeout=35)
            assert data["type"] == "heartbeat"
            assert "timestamp" in data["data"]


class TestConnectionMetrics:
    """Test connection metrics tracking"""

    def test_connection_metrics_recorded(self, client):
        """Test that metrics are recorded for connections"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            websocket.send_json({"type": "ping"})
            websocket.receive_json()  # Pong response

            # Check status for metrics
            websocket.send_json({"type": "get_status"})
            response = websocket.receive_json()

            assert response["data"]["messages_sent"] >= 1
            assert response["data"]["messages_received"] >= 1
            assert response["data"]["avg_latency_ms"] >= 0


class TestMultipleConnections:
    """Test multiple concurrent connections"""

    def test_multiple_concurrent_connections(self, client):
        """Test multiple concurrent WebSocket connections"""
        connections = []

        try:
            # Create 3 concurrent connections
            for i in range(3):
                conn = client.websocket_connect("/ws/")
                conn.__enter__()
                conn.receive_json()  # Connection message
                connections.append(conn)

            # Send a message on first connection
            connections[0].send_json({"type": "ping"})
            response = connections[0].receive_json()
            assert response["type"] == "pong"

            # Send on second connection
            connections[1].send_json({"type": "ping"})
            response = connections[1].receive_json()
            assert response["type"] == "pong"

        finally:
            for conn in connections:
                try:
                    conn.__exit__(None, None, None)
                except Exception:
                    pass


class TestErrorHandling:
    """Test error handling and recovery"""

    def test_websocket_invalid_json(self, client):
        """Test handling of invalid JSON"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            # This will be handled by FastAPI
            # Invalid JSON should close the connection or raise an error
            try:
                websocket.send_text("invalid json {")
                # Connection might close
            except Exception:
                pass  # Expected

    def test_websocket_timeout_recovery(self, client):
        """Test connection recovery after timeout"""
        with client.websocket_connect("/ws/") as websocket:
            websocket.receive_json()  # Connection message

            # Connection should still be responsive after timeout
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"


class TestConnectionManager:
    """Test ConnectionManager class directly"""

    @pytest.mark.asyncio
    async def test_connection_manager_metrics(self):
        """Test connection manager metrics aggregation"""
        manager_test = ConnectionManager()

        # Create mock metrics
        from app.api.websocket import ConnectionMetrics
        metrics1 = ConnectionMetrics()
        metrics1.record_latency(10.5)
        metrics1.record_latency(15.3)
        metrics1.messages_sent = 5
        metrics1.messages_received = 3

        metrics2 = ConnectionMetrics()
        metrics2.record_latency(12.2)
        metrics2.record_latency(14.1)
        metrics2.messages_sent = 7
        metrics2.messages_received = 4

        # Mock websockets
        class MockWebSocket:
            pass

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        manager_test.metrics[ws1] = metrics1
        manager_test.metrics[ws2] = metrics2
        manager_test.active_connections = [ws1, ws2]

        # Get aggregated metrics
        agg_metrics = manager_test.get_metrics()

        assert agg_metrics["total_connections"] == 2
        assert agg_metrics["total_messages_sent"] == 12
        assert agg_metrics["total_messages_received"] == 7
        assert agg_metrics["avg_latency_ms"] > 0
