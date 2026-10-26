import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import IntegrationConnection
from backend.app.config import settings

DEFAULT_CONNECTORS = [
    {
        "id": "stripe_simulated",
        "provider_name": "Stripe Gateway (Simulated)",
        "provider_type": "payment_gateway",
        "status": "SIMULATED",
        "description": "Deterministic mock payment adapter for charge retry, balance verification, and receipt simulation.",
        "settings_json": '{"mode": "SANDBOX", "webhook_configured": true, "live_keys_present": false}'
    },
    {
        "id": "shopify_simulated",
        "provider_name": "Shopify Store (Simulated)",
        "provider_type": "ecommerce_platform",
        "status": "SIMULATED",
        "description": "Mock eCommerce checkout adapter for abandoned cart recovery, coupon code generation, and link tracking.",
        "settings_json": '{"mode": "SANDBOX", "cart_abandonment_webhook": true, "live_keys_present": false}'
    },
    {
        "id": "quickbooks_mock",
        "provider_name": "QuickBooks Online",
        "provider_type": "accounting_system",
        "status": "NOT_CONNECTED",
        "description": "Live accounting synchronization. Not connected - requires OAuth2 credentials.",
        "settings_json": '{"oauth_configured": false, "sync_enabled": false}'
    },
    {
        "id": "xero_mock",
        "provider_name": "Xero Invoicing",
        "provider_type": "accounting_system",
        "status": "NOT_CONNECTED",
        "description": "Enterprise cloud accounting connector. Not connected - live API key required.",
        "settings_json": '{"api_key_present": false}'
    },
    {
        "id": "ollama_local",
        "provider_name": f"Ollama Local LLM ({settings.OLLAMA_MODEL})",
        "provider_type": "ai_reasoning_engine",
        "status": "CONNECTED",
        "description": "Local offline reasoning model running on http://localhost:11434 via strict Pydantic tool protocol.",
        "settings_json": json.dumps({"endpoint": settings.OLLAMA_BASE_URL, "model": settings.OLLAMA_MODEL, "local_offline": True})
    }
]

def seed_integrations_if_empty(db: Session):
    existing = db.query(IntegrationConnection).count()
    if existing == 0:
        now = datetime.now(timezone.utc)
        for conn_data in DEFAULT_CONNECTORS:
            conn = IntegrationConnection(
                id=conn_data["id"],
                provider_name=conn_data["provider_name"],
                provider_type=conn_data["provider_type"],
                status=conn_data["status"],
                description=conn_data["description"],
                last_sync_at=now if conn_data["status"] in ("SIMULATED", "CONNECTED") else None,
                settings_json=conn_data["settings_json"]
            )
            db.add(conn)
        db.commit()
