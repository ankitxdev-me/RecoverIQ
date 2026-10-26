from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import IntegrationConnection
from backend.app.schemas import IntegrationStatusResponse
from backend.app.integrations.registry import seed_integrations_if_empty
from backend.app.services.csv_importer import import_csv_data, ImportResult

router = APIRouter(tags=["Integrations & Import"])

@router.get("/api/integrations", response_model=List[IntegrationStatusResponse])
def get_integrations(db: Session = Depends(get_db)):
    seed_integrations_if_empty(db)
    return db.query(IntegrationConnection).all()

@router.post("/api/import/csv", response_model=ImportResult)
async def upload_csv_file(
    file: UploadFile = File(...),
    record_type: str = Form(..., description="payments, invoices, or checkouts"),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file.")

    content_bytes = await file.read()
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("latin-1")

    res = import_csv_data(db=db, file_content=content_str, record_type=record_type)
    return res
