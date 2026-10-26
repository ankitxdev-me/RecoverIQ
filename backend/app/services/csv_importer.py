import csv
import io
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.models import Customer, Transaction, Invoice, Checkout, Order
from backend.app.engine.recovery_engine import RecoveryEngine
from backend.app.services.audit_service import log_audit

class ImportResult(BaseModel):
    record_type: str
    total_rows: int
    imported_rows: int
    skipped_duplicates: int
    error_count: int
    errors: List[str]
    new_cases_detected: int

def parse_amount_to_cents(amount_str: str) -> int:
    """
    Safely parses an amount string (e.g. '$149.99', '149.99', '2500')
    into integer minor units (cents). Avoids float precision drift.
    """
    cleaned = re.sub(r"[^\d.-]", "", amount_str.strip())
    if not cleaned:
        raise ValueError("Empty or invalid amount")
    
    parts = cleaned.split(".")
    if len(parts) == 1:
        return int(parts[0]) * 100
    elif len(parts) == 2:
        dollars = int(parts[0]) if parts[0] else 0
        cents_part = parts[1][:2].ljust(2, "0")
        cents = int(cents_part)
        return (dollars * 100) + (cents if dollars >= 0 else -cents)
    else:
        raise ValueError(f"Malformed amount '{amount_str}'")

def parse_date(date_str: str) -> datetime:
    """Parses common ISO or date formats into UTC datetime."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format '{date_str}'")

def get_or_create_customer(
    db: Session,
    customer_ref: str,
    name: str = "Anonymous",
    email: str = "unknown@example.com",
    phone: str = None
) -> Customer:
    cust = db.query(Customer).filter(Customer.customer_ref == customer_ref).first()
    if not cust:
        cust = Customer(
            customer_ref=customer_ref,
            name=name or f"Customer {customer_ref}",
            email=email or f"{customer_ref}@example.com",
            phone=phone
        )
        db.add(cust)
        db.flush()
    return cust

def import_csv_data(db: Session, file_content: str, record_type: str) -> ImportResult:
    """
    Imports and validates CSV rows for payments, invoices, or checkouts.
    Rejects malformed rows with clear diagnostic messages.
    Prevents duplicates.
    Runs RecoveryEngine detection afterwards.
    """
    reader = csv.DictReader(io.StringIO(file_content))
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]

    errors: List[str] = []
    imported = 0
    skipped_duplicates = 0
    row_idx = 1  # header is row 1

    rec_type = record_type.lower()

    if rec_type in ("payment", "payments", "transaction", "transactions"):
        required_cols = {"external_id", "customer_ref", "amount", "status"}
        if not required_cols.issubset(set(fieldnames)):
            missing = required_cols - set(fieldnames)
            return ImportResult(
                record_type="payments",
                total_rows=0,
                imported_rows=0,
                skipped_duplicates=0,
                error_count=1,
                errors=[f"Missing required columns in CSV header: {', '.join(missing)}"],
                new_cases_detected=0
            )

        for raw_row in reader:
            row_idx += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            ext_id = row.get("external_id")
            cust_ref = row.get("customer_ref")
            status = row.get("status", "").upper()

            if not ext_id or not cust_ref:
                errors.append(f"Row {row_idx}: external_id and customer_ref cannot be empty.")
                continue

            # Check duplicate
            if db.query(Transaction).filter(Transaction.external_id == ext_id).first():
                skipped_duplicates += 1
                continue

            try:
                amount_cents = parse_amount_to_cents(row.get("amount", "0"))
            except Exception as e:
                errors.append(f"Row {row_idx}: Invalid amount '{row.get('amount')}': {str(e)}")
                continue

            if amount_cents <= 0:
                errors.append(f"Row {row_idx}: Amount must be positive.")
                continue

            tx_date = datetime.now(timezone.utc)
            if row.get("created_at"):
                try:
                    tx_date = parse_date(row.get("created_at"))
                except Exception as e:
                    errors.append(f"Row {row_idx}: Invalid date: {str(e)}")
                    continue

            customer = get_or_create_customer(
                db,
                customer_ref=cust_ref,
                name=row.get("customer_name") or f"Customer {cust_ref}",
                email=row.get("customer_email") or f"{cust_ref}@example.com"
            )

            tx = Transaction(
                external_id=ext_id,
                customer_id=customer.id,
                provider=row.get("provider", "stripe_simulated"),
                amount_cents=amount_cents,
                currency=row.get("currency", "USD").upper(),
                status=status,
                failure_code=row.get("failure_code"),
                failure_reason=row.get("failure_reason"),
                created_at=tx_date
            )
            db.add(tx)
            imported += 1

    elif rec_type in ("invoice", "invoices"):
        required_cols = {"invoice_number", "customer_ref", "amount", "status"}
        if not required_cols.issubset(set(fieldnames)):
            missing = required_cols - set(fieldnames)
            return ImportResult(
                record_type="invoices",
                total_rows=0,
                imported_rows=0,
                skipped_duplicates=0,
                error_count=1,
                errors=[f"Missing required columns in CSV header: {', '.join(missing)}"],
                new_cases_detected=0
            )

        for raw_row in reader:
            row_idx += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            inv_num = row.get("invoice_number")
            cust_ref = row.get("customer_ref")
            status = row.get("status", "").upper()

            if not inv_num or not cust_ref:
                errors.append(f"Row {row_idx}: invoice_number and customer_ref cannot be empty.")
                continue

            if db.query(Invoice).filter(Invoice.invoice_number == inv_num).first():
                skipped_duplicates += 1
                continue

            try:
                amount_cents = parse_amount_to_cents(row.get("amount", "0"))
            except Exception as e:
                errors.append(f"Row {row_idx}: Invalid amount: {str(e)}")
                continue

            due_date = datetime.now(timezone.utc)
            if row.get("due_date"):
                try:
                    due_date = parse_date(row.get("due_date"))
                except Exception as e:
                    errors.append(f"Row {row_idx}: Invalid due_date: {str(e)}")
                    continue

            days_overdue = 0
            if row.get("days_overdue"):
                try:
                    days_overdue = int(row.get("days_overdue"))
                except Exception:
                    days_overdue = 0
            elif status == "OVERDUE":
                now = datetime.now(timezone.utc)
                days_overdue = max(0, (now - due_date).days)

            customer = get_or_create_customer(
                db,
                customer_ref=cust_ref,
                name=row.get("customer_name") or f"Customer {cust_ref}",
                email=row.get("customer_email") or f"{cust_ref}@example.com"
            )

            inv = Invoice(
                invoice_number=inv_num,
                customer_id=customer.id,
                amount_cents=amount_cents,
                currency=row.get("currency", "USD").upper(),
                status=status,
                due_date=due_date,
                days_overdue=days_overdue,
                created_at=datetime.now(timezone.utc)
            )
            db.add(inv)
            imported += 1

    elif rec_type in ("checkout", "checkouts", "cart", "abandoned_checkouts"):
        required_cols = {"checkout_token", "customer_ref", "amount"}
        if not required_cols.issubset(set(fieldnames)):
            missing = required_cols - set(fieldnames)
            return ImportResult(
                record_type="checkouts",
                total_rows=0,
                imported_rows=0,
                skipped_duplicates=0,
                error_count=1,
                errors=[f"Missing required columns in CSV header: {', '.join(missing)}"],
                new_cases_detected=0
            )

        for raw_row in reader:
            row_idx += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            token = row.get("checkout_token")
            cust_ref = row.get("customer_ref")
            status = row.get("status", "ABANDONED").upper()

            if not token or not cust_ref:
                errors.append(f"Row {row_idx}: checkout_token and customer_ref cannot be empty.")
                continue

            if db.query(Checkout).filter(Checkout.checkout_token == token).first():
                skipped_duplicates += 1
                continue

            try:
                amount_cents = parse_amount_to_cents(row.get("amount", "0"))
            except Exception as e:
                errors.append(f"Row {row_idx}: Invalid amount: {str(e)}")
                continue

            abandoned_at = datetime.now(timezone.utc)
            if row.get("abandoned_at"):
                try:
                    abandoned_at = parse_date(row.get("abandoned_at"))
                except Exception as e:
                    errors.append(f"Row {row_idx}: Invalid abandoned_at date: {str(e)}")
                    continue

            cart_items = 1
            try:
                cart_items = int(row.get("cart_items_count", "1"))
            except Exception:
                cart_items = 1

            customer = get_or_create_customer(
                db,
                customer_ref=cust_ref,
                name=row.get("customer_name") or f"Customer {cust_ref}",
                email=row.get("customer_email") or f"{cust_ref}@example.com"
            )

            chk = Checkout(
                checkout_token=token,
                customer_id=customer.id,
                cart_items_count=cart_items,
                amount_cents=amount_cents,
                currency=row.get("currency", "USD").upper(),
                status=status,
                abandoned_at=abandoned_at,
                last_activity_at=abandoned_at
            )
            db.add(chk)
            imported += 1

    else:
        return ImportResult(
            record_type=record_type,
            total_rows=0,
            imported_rows=0,
            skipped_duplicates=0,
            error_count=1,
            errors=[f"Unknown record type '{record_type}'. Supported: payments, invoices, checkouts."],
            new_cases_detected=0
        )

    db.commit()

    # Automatically trigger recovery engine case detection on newly imported records
    engine = RecoveryEngine(db)
    new_cases = engine.sync_and_detect_cases()

    # Log audit event
    log_audit(
        db,
        event_type="CSV_IMPORTED",
        actor="HUMAN_OPERATOR",
        description=f"CSV import completed for {record_type}: {imported} rows imported, {skipped_duplicates} duplicates skipped, {len(errors)} errors. {new_cases} recovery cases detected.",
        is_simulated=True,
        metadata={"record_type": record_type, "imported": imported, "new_cases": new_cases}
    )

    return ImportResult(
        record_type=record_type,
        total_rows=imported + skipped_duplicates + len(errors),
        imported_rows=imported,
        skipped_duplicates=skipped_duplicates,
        error_count=len(errors),
        errors=errors[:20],  # cap to first 20 errors
        new_cases_detected=new_cases
    )
