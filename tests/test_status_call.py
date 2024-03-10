from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
import pytest
from app.main import app

@pytest.mark.anyio
async def test_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/status/")
    assert response.status_code == 200
    assert "status" in response.json()
