import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.agent.tools import execute_tool_safely
from backend.app.agent.ollama_client import OllamaClient
from backend.app.seed import reset_and_seed_database

@pytest.fixture
def seeded_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    reset_and_seed_database(session)
    yield session
    session.close()

def test_tool_dashboard_summary(seeded_db):
    result = execute_tool_safely("get_dashboard_summary", {}, seeded_db)
    assert "revenue_at_risk_display" in result
    assert "confirmed_live_recovered_display" in result
    assert "simulated_recovered_display" in result
    assert result["simulation_mode"] is True

def test_tool_list_cases(seeded_db):
    result = execute_tool_safely("list_recovery_cases", {"limit": 3}, seeded_db)
    assert "cases" in result
    assert len(result["cases"]) == 3
    # Check that highest priority comes first
    assert result["cases"][0]["priority_score"] >= result["cases"][1]["priority_score"]

def test_tool_investigate_case(seeded_db):
    result = execute_tool_safely("investigate_case", {"case_id": "CASE-PAY-1001"}, seeded_db)
    assert result["case_id"] == "CASE-PAY-1001"
    assert result["amount_display"] == "$1,450.00"
    assert "is_eligible_for_recovery" in result
    assert "customer" in result

def test_tool_draft_customer_message(seeded_db):
    result = execute_tool_safely("draft_customer_message", {"case_id": "CASE-PAY-1001", "tone": "polite"}, seeded_db)
    assert "subject" in result
    assert "body" in result
    assert "1,450.00" in result["subject"] or "1,450.00" in result["body"]

def test_invalid_tool_name_returns_error(seeded_db):
    result = execute_tool_safely("unauthorized_shell_command", {"command": "ls"}, seeded_db)
    assert "error" in result

def test_invalid_tool_arguments_handled_gracefully(seeded_db):
    # Missing required argument case_id
    result = execute_tool_safely("investigate_case", {}, seeded_db)
    assert "error" in result

def test_deterministic_fallback_when_ollama_offline(seeded_db):
    # Point client to a port where Ollama is definitely not running
    offline_client = OllamaClient(base_url="http://localhost:59999", model="qwen2.5:3b")
    
    # Query summary
    resp = offline_client.run_agent_turn(
        user_message="What is the total revenue at risk?",
        case_id=None,
        db=seeded_db
    )
    assert resp.source == "deterministic_fallback"
    assert "Revenue at Risk" in resp.reply
    assert len(resp.tools_called) >= 1

    # Query priority cases
    resp_cases = offline_client.run_agent_turn(
        user_message="Which five cases should I handle first?",
        case_id=None,
        db=seeded_db
    )
    assert resp_cases.source == "deterministic_fallback"
    assert "Top Priority Recovery Cases" in resp_cases.reply
