from fastapi.testclient import TestClient

from sentarr.main import app

client = TestClient(app)


def test_notification_test_endpoint() -> None:
    response = client.post("/api/v1/notifications/test", json={"title": "Test", "body": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "sent" in data
