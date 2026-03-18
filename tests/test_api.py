from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -----------------------
# Health Check Test
# -----------------------

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "API is working"


# -----------------------
# Ingest Endpoint Test
# -----------------------

def test_ingest_snapshot():
    payload = {
        "patient_id": "TEST_P1",
        "clinic_id": "TEST_C1",
        "source": "test_source",
        "medications": [
            {"name": "Lisinopril", "dose": "10 mg", "status": "active"}
        ]
    }
def test_unresolved_report():

    response = client.get("/report/C001")

    assert response.status_code == 200

    data = response.json()

    assert "clinic_id" in data
    assert "patients_with_unresolved_conflicts" in data

    response = client.post("/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "snapshot_id" in data
    assert "version" in data


# -----------------------
# Patient History Test
# -----------------------

def test_patient_history():
    response = client.get("/patient/TEST_P1/history")
    assert response.status_code == 200