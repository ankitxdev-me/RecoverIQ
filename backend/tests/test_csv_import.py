import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Transaction, RecoveryCase
from backend.app.services.csv_importer import import_csv_data

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_csv_import_payments_success(test_db):
    csv_content = """external_id,customer_ref,customer_name,customer_email,amount,currency,status,failure_code,failure_reason
tx_csv_1,CUST-A,Alpha Co,alpha@example.com,500.00,USD,FAILED,insufficient_funds,Declined
tx_csv_2,CUST-B,Beta Co,beta@example.com,750.50,USD,FAILED,expired_card,Card expired
"""
    result = import_csv_data(test_db, csv_content, "payments")
    assert result.imported_rows == 2
    assert result.error_count == 0
    assert result.skipped_duplicates == 0
    assert result.new_cases_detected == 2

    # Check transactions in DB
    tx1 = test_db.query(Transaction).filter(Transaction.external_id == "tx_csv_1").first()
    assert tx1 is not None
    assert tx1.amount_cents == 50000

    # Check recovery cases created
    cases = test_db.query(RecoveryCase).all()
    assert len(cases) == 2

def test_csv_duplicate_rejection(test_db):
    csv_content = """external_id,customer_ref,customer_name,customer_email,amount,status
tx_csv_dup,CUST-DUP,Dup Corp,dup@example.com,200.00,FAILED
"""
    res1 = import_csv_data(test_db, csv_content, "payments")
    assert res1.imported_rows == 1
    assert res1.skipped_duplicates == 0

    # Import identical row again
    res2 = import_csv_data(test_db, csv_content, "payments")
    assert res2.imported_rows == 0
    assert res2.skipped_duplicates == 1

def test_csv_malformed_rows_handled_safely(test_db):
    csv_content = """external_id,customer_ref,customer_name,customer_email,amount,status
,CUST-X,Missing ID,x@example.com,100.00,FAILED
tx_valid,CUST-Y,Valid Corp,y@example.com,300.00,FAILED
tx_bad_amt,CUST-Z,Bad Amt,z@example.com,NOT_AN_AMOUNT,FAILED
"""
    res = import_csv_data(test_db, csv_content, "payments")
    assert res.imported_rows == 1  # Only tx_valid should succeed
    assert res.error_count == 2
    assert any("external_id and customer_ref cannot be empty" in e for e in res.errors)
    assert any("Invalid amount" in e for e in res.errors)
