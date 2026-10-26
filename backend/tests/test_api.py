import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.seed import reset_and_seed_database

@pytest.fixture
def client():
    # Use StaticPool so all threads/sessions share the exact same in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    reset_and_seed_database(session)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    session.close()

def test_api_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database_ok"] is True
    assert "RecoverIQ" in data["app_name"]

def test_api_dashboard_summary(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "revenue_at_risk_cents" in data
    assert "simulated_recovered_cents" in data
    assert "confirmed_live_recovered_cents" in data
    # Verify that live and simulated are separated
    assert data["simulated_recovered_cents"] > 0
    assert data["simulation_mode"] is True

def test_api_cases_list_and_search(client):
    # List all
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) >= 5

    # Filter by source_type
    resp_pay = client.get("/api/cases?source_type=failed_payment")
    assert resp_pay.status_code == 200
    for c in resp_pay.json():
        assert c["source_type"] == "failed_payment"

    # Search by keyword
    resp_search = client.get("/api/cases?search=Acme")
    assert resp_search.status_code == 200
    assert len(resp_search.json()) >= 1
    assert "Acme" in resp_search.json()[0]["customer"]["name"]

def test_api_get_single_case(client):
    resp = client.get("/api/cases/CASE-PAY-1001")
    assert resp.status_code == 200
    case = resp.json()
    assert case["id"] == "CASE-PAY-1001"
    assert case["amount_cents"] == 145000

def test_api_case_not_found(client):
    resp = client.get("/api/cases/CASE-NONEXISTENT-999")
    assert resp.status_code == 404

def test_api_approvals_workflow(client):
    # 1. Fetch pending approvals (Case 5 was pre-seeded as pending approval)
    resp = client.get("/api/approvals")
    assert resp.status_code == 200
    approvals = resp.json()
    pending = [a for a in approvals if a["status"] == "PENDING"]
    assert len(pending) >= 1
    act_id = pending[0]["action_id"]

    # 2. Approve action
    appr_resp = client.post(f"/api/actions/{act_id}/approve", json={"decision": "APPROVE", "reason": "Authorized by supervisor"})
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"

    # 3. Execute action
    exec_resp = client.post(f"/api/actions/{act_id}/execute", json={"simulated_outcome": "SUCCESS"})
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "EXECUTED"

    # 4. Verify outcome
    ver_resp = client.post(f"/api/actions/{act_id}/verify", json={})
    assert ver_resp.status_code == 200
    assert ver_resp.json()["verification_status"] == "VERIFIED_CONFIRMED"

def test_api_demo_reset(client):
    resp = client.post("/api/demo/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Verify seed data is intact
    cases_resp = client.get("/api/cases")
    assert len(cases_resp.json()) >= 5
