import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest.mark.asyncio
async def test_health_check_returns_200():
    """Test health check endpoint returns 200"""
    # Initialize database for test
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test metrics endpoint returns data"""
    # Initialize database for test
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "active_tickets" in data
    assert "messages_last_hour" in data
    assert "timestamp" in data
