import sqlite3
import json
import re
import os
import uuid
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models import Customer, Transaction, Invoice, Checkout, RecoveryCase, AuditEvent
from backend.app.engine.recovery_engine import RecoveryEngine
from backend.app.engine.priority import calculate_priority_score
from backend.app.engine.eligibility import determine_recommended_action
from backend.app.services.audit_service import log_audit
from backend.app.services.csv_importer import parse_amount_to_cents, parse_date, get_or_create_customer
from backend.app.agent.ollama_client import OllamaClient

class BusinessAnomalyReport:
    def __init__(self):
        self.total_records_inspected = 0
        self.customers_imported = 0
        self.failed_payments_detected = 0
        self.overdue_invoices_detected = 0
        self.abandoned_checkouts_detected = 0
        self.total_loss_at_risk_cents = 0
        self.anomalies_detected: List[Dict[str, Any]] = []
        self.cases_created = 0
        self.ai_strategic_diagnosis = ""

def crawl_sqlite_database(db: Session, sqlite_file_bytes: bytes, wipe_demo_data: bool = False) -> Dict[str, Any]:
    """
    Crawls an uploaded business SQLite database (.db / .sqlite / .sqlite3).
    Inspects user, transaction, invoice, and cart tables.
    Imports actual business entities, calculates abnormalities, and creates prioritized recovery cases.
    """
    if wipe_demo_data:
        # Clear out existing demo data so the system runs strictly on real business data
        clear_all_business_data(db)

    # Save to temporary file to inspect with sqlite3
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(sqlite_file_bytes)
        tmp_path = tmp.name

    report = BusinessAnomalyReport()

    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row["name"] for row in cursor.fetchall()]

        # Helper to find column matching patterns
        def find_column(cols: List[str], patterns: List[str]) -> Optional[str]:
            for p in patterns:
                for c in cols:
                    if re.search(p, c, re.IGNORECASE):
                        return c
            return None

        # 1. Crawl Customer / User Tables
        customer_id_map: Dict[str, int] = {}
        for tbl in tables:
            if any(k in tbl.lower() for k in ("customer", "user", "client", "account", "member")):
                cursor.execute(f"PRAGMA table_info({tbl});")
                cols = [c["name"] for c in cursor.fetchall()]
                
                id_col = find_column(cols, [r"^id$", r"customer_id", r"user_id", r"ref"]) or cols[0]
                name_col = find_column(cols, [r"name", r"full_name", r"username"])
                email_col = find_column(cols, [r"email", r"mail"])
                phone_col = find_column(cols, [r"phone", r"mobile", r"contact"])

                cursor.execute(f"SELECT * FROM {tbl} LIMIT 500;")
                for row in cursor.fetchall():
                    raw_id = str(row[id_col]) if id_col in row.keys() else str(uuid.uuid4())[:8]
                    raw_name = str(row[name_col]) if name_col and name_col in row.keys() and row[name_col] else f"Business Client {raw_id}"
                    raw_email = str(row[email_col]) if email_col and email_col in row.keys() and row[email_col] else f"client_{raw_id}@company.com"
                    raw_phone = str(row[phone_col]) if phone_col and phone_col in row.keys() and row[phone_col] else None

                    cust = get_or_create_customer(db, customer_ref=f"CUST-{raw_id}", name=raw_name, email=raw_email, phone=raw_phone)
                    customer_id_map[raw_id] = cust.id
                    customer_id_map[str(cust.id)] = cust.id
                    report.customers_imported += 1
                    report.total_records_inspected += 1

        # 2. Crawl Payments / Transactions Tables for Failures & Declines
        failure_reasons_counter: Dict[str, int] = {}
        for tbl in tables:
            if any(k in tbl.lower() for k in ("payment", "transact", "charge", "billing", "order")):
                cursor.execute(f"PRAGMA table_info({tbl});")
                cols = [c["name"] for c in cursor.fetchall()]

                id_col = find_column(cols, [r"^id$", r"transact.*id", r"charge_id", r"external_id", r"order_id"]) or cols[0]
                cust_col = find_column(cols, [r"customer.*id", r"user.*id", r"client.*id"])
                amt_col = find_column(cols, [r"amount", r"total", r"price", r"value"])
                status_col = find_column(cols, [r"status", r"state", r"result"])
                reason_col = find_column(cols, [r"reason", r"failure", r"error", r"code", r"message"])
                date_col = find_column(cols, [r"created", r"date", r"timestamp", r"time"])

                cursor.execute(f"SELECT * FROM {tbl} LIMIT 1000;")
                for row in cursor.fetchall():
                    report.total_records_inspected += 1
                    status_val = str(row[status_col]).upper() if status_col and status_col in row.keys() and row[status_col] else ""
                    
                    # Detect payment abnormalities: failed, declined, error, charge_back, expired
                    is_failure = any(f in status_val for f in ("FAIL", "DECLIN", "ERR", "DROP", "REJECT", "UNPAID"))
                    
                    if is_failure:
                        raw_ext_id = str(row[id_col]) if id_col in row.keys() else f"tx_live_{uuid.uuid4().hex[:8]}"
                        raw_cust_ref = str(row[cust_col]) if cust_col and cust_col in row.keys() and row[cust_col] else "DEFAULT_CLIENT"
                        target_cust_id = customer_id_map.get(raw_cust_ref) or (db.query(Customer).first().id if db.query(Customer).first() else 1)

                        raw_amt = str(row[amt_col]) if amt_col and amt_col in row.keys() and row[amt_col] else "100.00"
                        amt_cents = parse_amount_to_cents(raw_amt)
                        raw_reason = str(row[reason_col]) if reason_col and reason_col in row.keys() and row[reason_col] else "Card processor decline"
                        failure_reasons_counter[raw_reason] = failure_reasons_counter.get(raw_reason, 0) + 1

                        tx_date = datetime.now(timezone.utc)
                        if date_col and date_col in row.keys() and row[date_col]:
                            try:
                                tx_date = parse_date(str(row[date_col]))
                            except Exception:
                                pass

                        # Check if transaction already imported
                        if not db.query(Transaction).filter(Transaction.external_id == raw_ext_id).first():
                            tx = Transaction(
                                external_id=raw_ext_id,
                                customer_id=target_cust_id,
                                provider="business_db_crawled",
                                amount_cents=amt_cents,
                                currency="USD",
                                status="FAILED",
                                failure_code=raw_reason[:64],
                                failure_reason=raw_reason,
                                created_at=tx_date
                            )
                            db.add(tx)
                            report.failed_payments_detected += 1
                            report.total_loss_at_risk_cents += amt_cents

        # 3. Crawl Invoices / Accounts Receivable Tables for Overdue Debt
        for tbl in tables:
            if any(k in tbl.lower() for k in ("invoice", "bill", "receivable")):
                cursor.execute(f"PRAGMA table_info({tbl});")
                cols = [c["name"] for c in cursor.fetchall()]

                inv_col = find_column(cols, [r"^id$", r"invoice.*num", r"inv_id", r"number"]) or cols[0]
                cust_col = find_column(cols, [r"customer.*id", r"user.*id", r"client.*id"])
                amt_col = find_column(cols, [r"amount", r"total", r"balance", r"due"])
                status_col = find_column(cols, [r"status", r"state"])
                due_col = find_column(cols, [r"due_date", r"due", r"deadline"])

                cursor.execute(f"SELECT * FROM {tbl} LIMIT 500;")
                for row in cursor.fetchall():
                    report.total_records_inspected += 1
                    status_val = str(row[status_col]).upper() if status_col and status_col in row.keys() and row[status_col] else ""
                    
                    is_overdue = any(o in status_val for o in ("OVERDUE", "UNPAID", "LATE", "PAST_DUE", "OPEN"))
                    if is_overdue:
                        raw_inv_num = str(row[inv_col]) if inv_col in row.keys() else f"INV-REAL-{uuid.uuid4().hex[:6]}"
                        raw_cust_ref = str(row[cust_col]) if cust_col and cust_col in row.keys() and row[cust_col] else "DEFAULT_CLIENT"
                        target_cust_id = customer_id_map.get(raw_cust_ref) or (db.query(Customer).first().id if db.query(Customer).first() else 1)

                        amt_cents = parse_amount_to_cents(str(row[amt_col]) if amt_col and amt_col in row.keys() else "250.00")
                        due_date = datetime.now(timezone.utc) - timedelta(days=21)
                        if due_col and due_col in row.keys() and row[due_col]:
                            try:
                                due_date = parse_date(str(row[due_col]))
                            except Exception:
                                pass

                        days_overdue = max(1, (datetime.now(timezone.utc) - due_date).days)

                        if not db.query(Invoice).filter(Invoice.invoice_number == raw_inv_num).first():
                            inv = Invoice(
                                invoice_number=raw_inv_num,
                                customer_id=target_cust_id,
                                amount_cents=amt_cents,
                                currency="USD",
                                status="OVERDUE",
                                due_date=due_date,
                                days_overdue=days_overdue,
                                created_at=datetime.now(timezone.utc)
                            )
                            db.add(inv)
                            report.overdue_invoices_detected += 1
                            report.total_loss_at_risk_cents += amt_cents

        # 4. Crawl Carts / Checkout Sessions for Abandonment
        for tbl in tables:
            if any(k in tbl.lower() for k in ("cart", "checkout", "session", "basket")):
                cursor.execute(f"PRAGMA table_info({tbl});")
                cols = [c["name"] for c in cursor.fetchall()]

                tok_col = find_column(cols, [r"token", r"^id$", r"session.*id", r"cart.*id"]) or cols[0]
                cust_col = find_column(cols, [r"customer.*id", r"user.*id", r"email"])
                amt_col = find_column(cols, [r"amount", r"total", r"subtotal", r"price"])
                status_col = find_column(cols, [r"status", r"abandoned"])

                cursor.execute(f"SELECT * FROM {tbl} LIMIT 500;")
                for row in cursor.fetchall():
                    report.total_records_inspected += 1
                    status_val = str(row[status_col]).upper() if status_col and status_col in row.keys() and row[status_col] else "ABANDONED"

                    if "ABANDON" in status_val or "DROP" in status_val or "INCOMPLETE" in status_val:
                        raw_token = str(row[tok_col]) if tok_col in row.keys() else f"chk_crawled_{uuid.uuid4().hex[:8]}"
                        raw_cust_ref = str(row[cust_col]) if cust_col and cust_col in row.keys() and row[cust_col] else "DEFAULT_CLIENT"
                        target_cust_id = customer_id_map.get(raw_cust_ref) or (db.query(Customer).first().id if db.query(Customer).first() else 1)

                        amt_cents = parse_amount_to_cents(str(row[amt_col]) if amt_col and amt_col in row.keys() else "120.00")

                        if not db.query(Checkout).filter(Checkout.checkout_token == raw_token).first():
                            chk = Checkout(
                                checkout_token=raw_token,
                                customer_id=target_cust_id,
                                cart_items_count=2,
                                amount_cents=amt_cents,
                                currency="USD",
                                status="ABANDONED",
                                abandoned_at=datetime.now(timezone.utc) - timedelta(hours=12),
                                last_activity_at=datetime.now(timezone.utc) - timedelta(hours=12)
                            )
                            db.add(chk)
                            report.abandoned_checkouts_detected += 1
                            report.total_loss_at_risk_cents += amt_cents

        conn.close()
        db.commit()

        # Run Recovery Engine to auto-detect and score all cases
        engine = RecoveryEngine(db)
        new_cases = engine.sync_and_detect_cases()
        report.cases_created = new_cases

        # Categorize business abnormalities
        if report.failed_payments_detected > 0:
            top_failure = max(failure_reasons_counter.items(), key=lambda x: x[1])[0] if failure_reasons_counter else "Gateway Decline"
            report.anomalies_detected.append({
                "type": "PAYMENT_GATEWAY_LEAKAGE",
                "severity": "CRITICAL" if report.failed_payments_detected >= 3 else "HIGH",
                "description": f"Detected {report.failed_payments_detected} failed customer transactions. Primary cluster: '{top_failure}'.",
                "action_recommended": "Simulated Smart Retries & Automated Card Update Dispatch"
            })

        if report.overdue_invoices_detected > 0:
            report.anomalies_detected.append({
                "type": "AGING_ACCOUNTS_RECEIVABLE",
                "severity": "CRITICAL",
                "description": f"Identified {report.overdue_invoices_detected} past-due invoices aging without settlement.",
                "action_recommended": "Staggered Dunning Escalation Schedule & Formal Review"
            })

        if report.abandoned_checkouts_detected > 0:
            report.anomalies_detected.append({
                "type": "CHECKOUT_CONVERSION_LEAK",
                "severity": "MEDIUM",
                "description": f"Found {report.abandoned_checkouts_detected} high-intent checkout sessions abandoned before payment.",
                "action_recommended": "Automated Cart Recovery Links with 10% Discount Incentive"
            })

        # Ask local Qwen model for executive diagnosis
        report.ai_strategic_diagnosis = generate_qwen_loss_audit_summary(report)

        log_audit(
            db=db,
            event_type="DATABASE_CRAWLED",
            actor="AI_CRAWLER_ENGINE",
            description=f"Crawled live business database: {report.total_records_inspected} records inspected. Generated {report.cases_created} prioritized recovery cases totaling ${report.total_loss_at_risk_cents/100:,.2f}.",
            is_simulated=False,
            metadata={"anomalies": report.anomalies_detected, "total_loss": report.total_loss_at_risk_cents}
        )

        return {
            "status": "success",
            "message": f"Successfully crawled business database. Inspected {report.total_records_inspected} rows and generated {report.cases_created} verified recovery cases.",
            "total_records_inspected": report.total_records_inspected,
            "customers_imported": report.customers_imported,
            "failed_payments_detected": report.failed_payments_detected,
            "overdue_invoices_detected": report.overdue_invoices_detected,
            "abandoned_checkouts_detected": report.abandoned_checkouts_detected,
            "total_loss_at_risk_display": f"${report.total_loss_at_risk_cents/100:,.2f}",
            "anomalies_detected": report.anomalies_detected,
            "new_cases_created": report.cases_created,
            "ai_strategic_diagnosis": report.ai_strategic_diagnosis
        }

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def crawl_json_business_data(db: Session, raw_json_str: str, wipe_demo_data: bool = False) -> Dict[str, Any]:
    """
    Crawls an uploaded business JSON export (Stripe events, billing exports, CRM dumps).
    Inspects customer, transaction, invoice, and cart items.
    """
    if wipe_demo_data:
        clear_all_business_data(db)

    report = BusinessAnomalyReport()
    try:
        data = json.loads(raw_json_str)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Invalid JSON file format: {str(e)}",
            "total_records_inspected": 0,
            "new_cases_created": 0
        }

    # Normalize data into collections
    customers_list = []
    transactions_list = []
    invoices_list = []
    checkouts_list = []

    if isinstance(data, dict):
        for k, v in data.items():
            k_lower = k.lower()
            if isinstance(v, list):
                if any(x in k_lower for x in ("cust", "user", "client")):
                    customers_list.extend(v)
                elif any(x in k_lower for x in ("transact", "pay", "charge")):
                    transactions_list.extend(v)
                elif any(x in k_lower for x in ("inv", "bill")):
                    invoices_list.extend(v)
                elif any(x in k_lower for x in ("cart", "checkout")):
                    checkouts_list.extend(v)
    elif isinstance(data, list):
        # Mixed list or transactions list
        for item in data:
            if isinstance(item, dict):
                if "invoice_number" in item or "due_date" in item:
                    invoices_list.append(item)
                elif "checkout_token" in item or "cart_items_count" in item:
                    checkouts_list.append(item)
                elif "amount_cents" in item or "amount" in item or "failure_code" in item:
                    transactions_list.append(item)
                elif "email" in item or "customer_id" in item:
                    customers_list.append(item)

    # 1. Process Customers
    customer_id_map: Dict[str, int] = {}
    for c in customers_list:
        report.total_records_inspected += 1
        raw_id = str(c.get("id") or c.get("customer_id") or c.get("customer_ref") or uuid.uuid4().hex[:8])
        name = str(c.get("name") or c.get("full_name") or f"Client {raw_id}")
        email = str(c.get("email") or f"client_{raw_id}@company.com")
        phone = c.get("phone")
        cust = get_or_create_customer(db, customer_ref=f"CUST-{raw_id}", name=name, email=email, phone=phone)
        customer_id_map[raw_id] = cust.id
        customer_id_map[str(cust.id)] = cust.id
        report.customers_imported += 1

    # 2. Process Transactions (Payment Failures)
    failure_reasons_counter: Dict[str, int] = {}
    for t in transactions_list:
        report.total_records_inspected += 1
        status = str(t.get("status", "")).upper()
        if any(f in status for f in ("FAIL", "DECLIN", "ERR", "DROP", "REJECT", "UNPAID")) or t.get("failure_code"):
            raw_ext = str(t.get("external_id") or t.get("id") or f"tx_json_{uuid.uuid4().hex[:8]}")
            raw_cust = str(t.get("customer_id") or t.get("customer_ref") or "DEFAULT")
            target_id = customer_id_map.get(raw_cust) or (db.query(Customer).first().id if db.query(Customer).first() else 1)
            raw_amt = str(t.get("amount_cents") or t.get("amount") or "100.00")
            amt_cents = parse_amount_to_cents(raw_amt)
            reason = str(t.get("failure_reason") or t.get("failure_code") or "Transaction card decline")
            failure_reasons_counter[reason] = failure_reasons_counter.get(reason, 0) + 1

            if not db.query(Transaction).filter(Transaction.external_id == raw_ext).first():
                tx = Transaction(
                    external_id=raw_ext,
                    customer_id=target_id,
                    provider=str(t.get("provider", "business_json_import")),
                    amount_cents=amt_cents,
                    currency=str(t.get("currency", "USD")),
                    status="FAILED",
                    failure_code=reason[:64],
                    failure_reason=reason,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(tx)
                report.failed_payments_detected += 1
                report.total_loss_at_risk_cents += amt_cents

    # 3. Process Invoices (Overdue)
    for inv in invoices_list:
        report.total_records_inspected += 1
        status = str(inv.get("status", "")).upper()
        if any(o in status for o in ("OVERDUE", "UNPAID", "LATE", "PAST_DUE", "OPEN")) or inv.get("days_overdue"):
            raw_num = str(inv.get("invoice_number") or inv.get("id") or f"INV-JSON-{uuid.uuid4().hex[:6]}")
            raw_cust = str(inv.get("customer_id") or inv.get("customer_ref") or "DEFAULT")
            target_id = customer_id_map.get(raw_cust) or (db.query(Customer).first().id if db.query(Customer).first() else 1)
            amt_cents = parse_amount_to_cents(str(inv.get("amount_cents") or inv.get("amount") or "250.00"))
            days = int(inv.get("days_overdue") or 14)

            if not db.query(Invoice).filter(Invoice.invoice_number == raw_num).first():
                inv_obj = Invoice(
                    invoice_number=raw_num,
                    customer_id=target_id,
                    amount_cents=amt_cents,
                    currency=str(inv.get("currency", "USD")),
                    status="OVERDUE",
                    due_date=datetime.now(timezone.utc) - timedelta(days=days),
                    days_overdue=days,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(inv_obj)
                report.overdue_invoices_detected += 1
                report.total_loss_at_risk_cents += amt_cents

    # 4. Process Checkouts (Abandoned)
    for c in checkouts_list:
        report.total_records_inspected += 1
        status = str(c.get("status", "ABANDONED")).upper()
        if any(a in status for a in ("ABANDON", "DROP", "INCOMPLETE")):
            raw_tok = str(c.get("checkout_token") or c.get("id") or f"chk_json_{uuid.uuid4().hex[:8]}")
            raw_cust = str(c.get("customer_id") or c.get("customer_ref") or "DEFAULT")
            target_id = customer_id_map.get(raw_cust) or (db.query(Customer).first().id if db.query(Customer).first() else 1)
            amt_cents = parse_amount_to_cents(str(c.get("amount_cents") or c.get("amount") or "99.00"))

            if not db.query(Checkout).filter(Checkout.checkout_token == raw_tok).first():
                chk_obj = Checkout(
                    checkout_token=raw_tok,
                    customer_id=target_id,
                    cart_items_count=int(c.get("cart_items_count") or 1),
                    amount_cents=amt_cents,
                    currency=str(c.get("currency", "USD")),
                    status="ABANDONED",
                    abandoned_at=datetime.now(timezone.utc) - timedelta(hours=10),
                    last_activity_at=datetime.now(timezone.utc) - timedelta(hours=10)
                )
                db.add(chk_obj)
                report.abandoned_checkouts_detected += 1
                report.total_loss_at_risk_cents += amt_cents

    db.commit()

    # Run engine to sync & detect
    engine = RecoveryEngine(db)
    report.cases_created = engine.sync_and_detect_cases()

    # Categorize anomalies
    if report.failed_payments_detected > 0:
        top_failure = max(failure_reasons_counter.items(), key=lambda x: x[1])[0] if failure_reasons_counter else "Card Decline"
        report.anomalies_detected.append({
            "type": "PAYMENT_GATEWAY_LEAKAGE",
            "severity": "CRITICAL" if report.failed_payments_detected >= 3 else "HIGH",
            "description": f"Detected {report.failed_payments_detected} failed charges. Top decline reason: '{top_failure}'.",
            "action_recommended": "Automated Retry Sequencing & Secure Payment Method Update Links"
        })

    if report.overdue_invoices_detected > 0:
        report.anomalies_detected.append({
            "type": "AGING_ACCOUNTS_RECEIVABLE",
            "severity": "CRITICAL",
            "description": f"Found {report.overdue_invoices_detected} overdue invoices causing working capital blockage.",
            "action_recommended": "Polite Multi-Tier Dunning Notices with Expedited Pay Link"
        })

    if report.abandoned_checkouts_detected > 0:
        report.anomalies_detected.append({
            "type": "CHECKOUT_CONVERSION_LEAK",
            "severity": "MEDIUM",
            "description": f"Identified {report.abandoned_checkouts_detected} high-intent shopping carts dropped before checkout.",
            "action_recommended": "Time-sensitive Cart Recovery Link with One-Click Checkout"
        })

    report.ai_strategic_diagnosis = generate_qwen_loss_audit_summary(report)

    log_audit(
        db=db,
        event_type="JSON_DATABASE_INGESTED",
        actor="AI_CRAWLER_ENGINE",
        description=f"Ingested business JSON data: {report.total_records_inspected} items inspected. Created {report.cases_created} recovery cases totaling ${report.total_loss_at_risk_cents/100:,.2f}.",
        is_simulated=False,
        metadata={"anomalies": report.anomalies_detected, "total_loss": report.total_loss_at_risk_cents}
    )

    return {
        "status": "success",
        "message": f"Successfully processed business JSON data. Inspected {report.total_records_inspected} items and generated {report.cases_created} verified recovery cases.",
        "total_records_inspected": report.total_records_inspected,
        "customers_imported": report.customers_imported,
        "failed_payments_detected": report.failed_payments_detected,
        "overdue_invoices_detected": report.overdue_invoices_detected,
        "abandoned_checkouts_detected": report.abandoned_checkouts_detected,
        "total_loss_at_risk_display": f"${report.total_loss_at_risk_cents/100:,.2f}",
        "anomalies_detected": report.anomalies_detected,
        "new_cases_created": report.cases_created,
        "ai_strategic_diagnosis": report.ai_strategic_diagnosis
    }


def clear_all_business_data(db: Session):
    """Purges all demo data so that only real ingested business records exist in the ledger."""
    from backend.app.models import ApprovalRecord, RecoveryAction, AuditEvent, RecoveryCase, Transaction, Invoice, Checkout, Customer
    db.query(ApprovalRecord).delete()
    db.query(RecoveryAction).delete()
    db.query(AuditEvent).delete()
    db.query(RecoveryCase).delete()
    db.query(Transaction).delete()
    db.query(Invoice).delete()
    db.query(Checkout).delete()
    db.query(Customer).delete()
    db.commit()


def generate_qwen_loss_audit_summary(report: BusinessAnomalyReport) -> str:
    """Invokes local Qwen model to produce executive audit diagnosis of real crawled data."""
    client = OllamaClient()
    is_healthy, _, _ = client.check_health()
    if not is_healthy:
        return (
            f"RecoverIQ Loss Audit: Identified ${report.total_loss_at_risk_cents/100:,.2f} in revenue leakage across "
            f"{report.failed_payments_detected} failed charges, {report.overdue_invoices_detected} overdue receivables, "
            f"and {report.abandoned_checkouts_detected} abandoned carts. Recovery actions have been created and prioritized."
        )

    prompt = (
        f"You are RecoverIQ Lead Financial Recovery Specialist. Analyze these real business crawl metrics:\n"
        f"- Total Revenue Leaked at Risk: ${report.total_loss_at_risk_cents/100:,.2f}\n"
        f"- Failed Payments: {report.failed_payments_detected}\n"
        f"- Overdue Invoices: {report.overdue_invoices_detected}\n"
        f"- Abandoned Carts: {report.abandoned_checkouts_detected}\n"
        f"Provide a concise executive revenue loss diagnosis (3-4 bullet points), identify the highest-urgency leakage point, "
        f"and confirm that all recovery workflows have been mapped to financial safety guardrails."
    )

    try:
        reply = client._call_ollama(
            messages=[
                {"role": "system", "content": "You are RecoverIQ Revenue Diagnostic Agent. Be concise, strategic, and professional."},
                {"role": "user", "content": prompt}
            ],
            use_tools=False
        )
        content = reply.get("content", "").strip()
        if not content and reply.get("thinking"):
            content = reply.get("thinking", "").strip()
        return content if content else (
            f"Executive Diagnosis: System detected ${report.total_loss_at_risk_cents/100:,.2f} in preventable losses. "
            f"Priority workflows have been established with automated retry scheduling and human approval safeguards."
        )
    except Exception:
        return (
            f"Executive Diagnosis: System detected ${report.total_loss_at_risk_cents/100:,.2f} in preventable losses. "
            f"Priority workflows have been established with automated retry scheduling and human approval safeguards."
        )

