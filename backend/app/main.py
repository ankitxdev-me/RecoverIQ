from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import RecoveryCase
from backend.app.seed import reset_and_seed_database
from backend.app.integrations.registry import seed_integrations_if_empty

# Routers
from backend.app.routers import (
    health, dashboard, cases, actions, approvals, agent, audit, integrations, demo, business, session
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize connectors if empty, but do NOT auto-seed dummy cases
    db = SessionLocal()
    try:
        seed_integrations_if_empty(db)
    finally:
        db.close()
    
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Deterministic AI Revenue Recovery Agent for Failed Payments, Overdue Invoices, and Abandoned Checkouts.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(cases.router)
app.include_router(actions.router)
app.include_router(approvals.router)
app.include_router(agent.router)
app.include_router(audit.router)
app.include_router(integrations.router)
app.include_router(demo.router)
app.include_router(business.router)
app.include_router(session.router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "simulation_mode": settings.SIMULATION_MODE,
        "docs": "/docs"
    }
