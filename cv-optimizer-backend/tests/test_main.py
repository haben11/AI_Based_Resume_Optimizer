from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_no_file():
    response = client.post("/api/v1/optimize/upload")
    assert response.status_code == 422  # Validation error (missing file)
