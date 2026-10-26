import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models import RecoveryCase, RecoveryAction, ApprovalRecord
from backend.app.agent.ollama_client import OllamaClient
from backend.app.agent.tools import execute_tool_safely
from backend.app.seed import reset_and_seed_database
from backend.app.config import settings

@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    reset_and_seed_database(session)
    yield session
    session.close()

def test_ollama_model_connection_and_availability():
    """Confirms model is connected and available at http://localhost:11434."""
    client = OllamaClient()
    assert client.model == settings.OLLAMA_MODEL
    assert "11434" in client.base_url

    is_healthy, err, details = client.check_health()
    assert is_healthy is True, f"Ollama connection check failed: {err}"
    assert details is not None
    model_names = [m.get("name") for m in details.get("models", [])]
    assert any(settings.OLLAMA_MODEL in name for name in model_names), f"{settings.OLLAMA_MODEL} not found in {model_names}"

def test_safety_boundary_unknown_tool_rejected(test_db):
    """Confirm unknown tool requests are strictly rejected."""
    result = execute_tool_safely("unauthorized_shell_execution", {"cmd": "rm -rf /"}, test_db)
    assert "error" in result
    assert "Unknown tool" in result["error"]

def test_safety_boundary_invalid_arguments_rejected(test_db):
    """Confirm invalid tool arguments are rejected by Pydantic validation."""
    # investigate_case requires 'case_id'
    result = execute_tool_safely("investigate_case", {}, test_db)
    assert "error" in result
    assert "failed" in result["error"].lower()

def test_safety_boundary_cannot_bypass_approval(test_db):
    """Confirm model cannot bypass approval rules for high-value cases."""
    # Case 5 is $12,500.00
    rec_res = execute_tool_safely("recommend_recovery_action", {"case_id": "CASE-PAY-5005"}, test_db)
    assert rec_res["requires_human_approval"] is True

def test_safety_boundary_simulation_segregation(test_db):
    """Confirm simulated outcomes are never counted as live recovered revenue."""
    summary = execute_tool_safely("get_dashboard_summary", {}, test_db)
    assert summary["simulation_mode"] is True
    # In seeded DB: Live is $850.00, Simulated is $720.00
    assert summary["confirmed_live_recovered_display"] == "$850.00"
    assert summary["simulated_recovered_display"] == "$720.00"
    assert summary["confirmed_live_recovered_display"] != summary["simulated_recovered_display"]

def test_realistic_agent_question_1_five_cases(test_db):
    """Q1: Which five recovery cases should I handle first, and why?"""
    client = OllamaClient()
    t0 = time.time()
    resp = client.run_agent_turn(
        user_message="Which five recovery cases should I handle first, and why?",
        case_id=None,
        db=test_db
    )
    elapsed = time.time() - t0

    assert resp.reply is not None
    assert len(resp.reply) > 50
    # Must list top priority cases
    assert "CASE-" in resp.reply
    assert len(resp.tools_called) >= 1 or resp.source == "deterministic_fallback"
    print(f"\n[EVAL Q1] Latency: {elapsed:.2f}s | Source: {resp.source} | Tools: {len(resp.tools_called)}")

def test_realistic_agent_question_2_failed_payment_priority(test_db):
    """Q2: Explain why this particular failed payment has high priority."""
    client = OllamaClient()
    t0 = time.time()
    resp = client.run_agent_turn(
        user_message="Explain why this particular failed payment has high priority.",
        case_id="CASE-PAY-1001",
        db=test_db
    )
    elapsed = time.time() - t0

    assert resp.reply is not None
    assert "CASE-PAY-1001" in resp.reply
    assert "1,450.00" in resp.reply or "1450" in resp.reply
    print(f"\n[EVAL Q2] Latency: {elapsed:.2f}s | Source: {resp.source} | Tools: {len(resp.tools_called)}")

def test_realistic_agent_question_3_revenue_at_risk(test_db):
    """Q3: What is the total revenue at risk?"""
    client = OllamaClient()
    t0 = time.time()
    resp = client.run_agent_turn(
        user_message="What is the total revenue at risk?",
        case_id=None,
        db=test_db
    )
    elapsed = time.time() - t0

    assert resp.reply is not None
    assert "$18,079.00" in resp.reply or "18,079" in resp.reply
    print(f"\n[EVAL Q3] Latency: {elapsed:.2f}s | Source: {resp.source} | Tools: {len(resp.tools_called)}")

def test_realistic_agent_question_4_investigate_invoice(test_db):
    """Q4: Investigate this invoice and recommend a safe next action."""
    client = OllamaClient()
    t0 = time.time()
    resp = client.run_agent_turn(
        user_message="Investigate this invoice and recommend a safe next action.",
        case_id="CASE-INV-2002",
        db=test_db
    )
    elapsed = time.time() - t0

    assert resp.reply is not None
    assert "CASE-INV-2002" in resp.reply
    print(f"\n[EVAL Q4] Latency: {elapsed:.2f}s | Source: {resp.source} | Tools: {len(resp.tools_called)}")

def test_realistic_agent_question_5_cases_awaiting_approval(test_db):
    """Q5: Show me which cases are awaiting approval."""
    client = OllamaClient()
    t0 = time.time()
    resp = client.run_agent_turn(
        user_message="Show me which cases are awaiting approval.",
        case_id=None,
        db=test_db
    )
    elapsed = time.time() - t0

    assert resp.reply is not None
    assert "CASE-PAY-5005" in resp.reply or "approval" in resp.reply.lower()
    print(f"\n[EVAL Q5] Latency: {elapsed:.2f}s | Source: {resp.source} | Tools: {len(resp.tools_called)}")
