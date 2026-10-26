import pytest
import os
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import RecoveryCase, Transaction, Invoice, Checkout
from backend.app.services.database_crawler import crawl_sqlite_database, crawl_json_business_data, clear_all_business_data

@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_crawl_sqlite_database(test_db):
    db_path = "backend/sample_data/real_business_database.db"
    assert os.path.exists(db_path), "Sample business db should exist"

    with open(db_path, "rb") as f:
        file_bytes = f.read()

    result = crawl_sqlite_database(db=test_db, sqlite_file_bytes=file_bytes, wipe_demo_data=True)
    assert result["status"] == "success"
    assert result["failed_payments_detected"] >= 4
    assert result["overdue_invoices_detected"] >= 3
    assert result["abandoned_checkouts_detected"] >= 3
    assert result["new_cases_created"] >= 10
    assert len(result["anomalies_detected"]) >= 3
    assert "Recover" in result["ai_strategic_diagnosis"] or "Diagnosis" in result["ai_strategic_diagnosis"] or len(result["ai_strategic_diagnosis"]) > 0

def test_crawl_json_business_data(test_db):
    json_path = "backend/sample_data/business_export.json"
    assert os.path.exists(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        raw_json = f.read()

    result = crawl_json_business_data(db=test_db, raw_json_str=raw_json, wipe_demo_data=True)
    assert result["status"] == "success"
    assert result["failed_payments_detected"] == 2
    assert result["overdue_invoices_detected"] == 2
    assert result["abandoned_checkouts_detected"] == 2
    assert result["new_cases_created"] == 6

def test_clear_all_business_data(test_db):
    json_path = "backend/sample_data/business_export.json"
    with open(json_path, "r", encoding="utf-8") as f:
        raw_json = f.read()
    crawl_json_business_data(db=test_db, raw_json_str=raw_json, wipe_demo_data=False)
    assert test_db.query(RecoveryCase).count() > 0

    clear_all_business_data(test_db)
    assert test_db.query(RecoveryCase).count() == 0
    assert test_db.query(Transaction).count() == 0
    assert test_db.query(Invoice).count() == 0
    assert test_db.query(Checkout).count() == 0

def test_api_business_upload(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    client = TestClient(app)

    db_path = "backend/sample_data/real_business_database.db"
    with open(db_path, "rb") as f:
        response = client.post(
            "/api/business/upload-database",
            files={"file": ("my_business.sqlite3", f, "application/octet-stream")},
            data={"wipe_demo": "true"}
        )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["new_cases_created"] > 0

    # Test connect software
    conn_res = client.post(
        "/api/business/connect-software",
        data={"provider": "stripe", "api_key": "sk_live_123456789abcdef", "environment": "live"}
    )
    assert conn_res.status_code == 200
    assert conn_res.json()["connection_status"] == "CONNECTED"

    # Test audit summary
    audit_res = client.get("/api/business/audit-summary")
    assert audit_res.status_code == 200
    assert audit_res.json()["total_recovery_cases"] > 0

    # Test clear demo data
    clear_res = client.post("/api/business/clear-demo-data")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "success"

    app.dependency_overrides.clear()
