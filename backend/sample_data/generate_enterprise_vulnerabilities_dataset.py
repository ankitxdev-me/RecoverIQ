import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta

def generate_datasets():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    os.makedirs(output_dir, exist_ok=True)
    
    db_vulnerabilities_path = os.path.join(output_dir, "apex_enterprise_business_vulnerabilities.db")
    json_vulnerabilities_path = os.path.join(output_dir, "apex_enterprise_vulnerabilities.json")
    
    # Also mirror to default real_business_database.db and business_export.json
    db_default_path = os.path.join(output_dir, "real_business_database.db")
    json_default_path = os.path.join(output_dir, "business_export.json")

    # -------------------------------------------------------------
    # 1. GENERATE SQLite DATABASE
    # -------------------------------------------------------------
    for target_db in (db_vulnerabilities_path, db_default_path):
        if os.path.exists(target_db):
            os.remove(target_db)

        conn = sqlite3.connect(target_db)
        cur = conn.cursor()

        # Company metadata table
        cur.execute("""
        CREATE TABLE business_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        meta = [
            ("company_name", "Apex Global Enterprise Cloud Inc"),
            ("industry", "B2B Cloud Infrastructure & Cybersecurity SaaS"),
            ("reporting_currency", "USD"),
            ("generated_at", datetime.now(timezone.utc).isoformat()),
            ("audit_status", "VULNERABILITIES_EMBEDDED_FOR_AI_DETECTION"),
            ("total_revenue_at_risk_preview", "$74,050.00")
        ]
        cur.executemany("INSERT INTO business_metadata VALUES (?, ?);", meta)

        # Users / Customers table
        cur.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            account_tier TEXT,
            created_at TEXT
        );
        """)
        users_data = [
            ("usr_apex_01", "Nexus HealthTech Enterprise (Marcus Vance)", "billing@nexushealth.org", "+1-415-555-0144", "ENTERPRISE", "2024-03-12"),
            ("usr_apex_02", "CyberPulse Security Systems (Devon Reed)", "devon@cyberpulse.net", "+1-312-555-0199", "MID_MARKET", "2024-06-20"),
            ("usr_apex_03", "Metropolis Infrastructure Group (David Sterling)", "finance@metropolis-infrastructure.com", "+1-212-555-0112", "STRATEGIC_GOV", "2023-11-05"),
            ("usr_apex_04", "Orbit Satellite Communications Ltd (Sir Arthur Finch)", "accounts@orbitsat.co.uk", "+44-20-7946-0922", "ENTERPRISE", "2024-01-18"),
            ("usr_apex_05", "Vanguard Aerospace Solutions (Capt. Ronald Hayes)", "procurement@vanguardaero.com", "+1-206-555-0187", "DEFENSE_AVIONICS", "2024-08-01"),
            ("usr_apex_06", "Synergy BioLabs (Dr. Elena Rostova)", "elena.rostova@synergybiolabs.com", "+1-617-555-0131", "HEALTHCARE_BIO", "2024-05-14"),
            ("usr_apex_07", "Solaria Energy International (Dirk Van Der Bilt)", "cfo@solariaenergy.eu", "+49-30-2312-5544", "RENEWABLE_UTILITY", "2023-09-30"),
            ("usr_apex_08", "Hyperion Media Cloud (Talia Chen)", "marcus@hyperionmedia.io", "+1-310-555-0165", "STREAMING_SAAS", "2024-04-22"),
            ("usr_apex_09", "QuantEdge High-Frequency Systems (Nikhil Rao)", "devops@quantedge.tech", "+1-646-555-0123", "FINTECH_HFT", "2024-02-10"),
            ("usr_apex_10", "Beacon Logistics Global (Kavita Sharma)", "kavita@beaconlog.com", "+1-404-555-0182", "LOGISTICS", "2024-07-08")
        ]
        cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?);", users_data)

        # Charges / Payment Transactions table (4 distinct failure vulnerabilities + 1 success baseline)
        cur.execute("""
        CREATE TABLE charges (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            failure_reason TEXT,
            created_at TEXT
        );
        """)
        charges_data = [
            ("ch_live_apex_901", "usr_apex_01", 14500.00, "FAILED", "Card expired or replaced by issuing bank - Zero retry attempts initiated (Silent recurring drop)", "2026-10-25 14:30:00"),
            ("ch_live_apex_902", "usr_apex_02", 6800.00, "FAILED", "Processor velocity check exceeded - Network fraud rule false positive lockout", "2026-10-24 18:15:00"),
            ("ch_live_apex_903", "usr_apex_07", 4950.00, "FAILED", "Cross-border transaction not permitted - Issuer foreign exchange settlement block", "2026-10-25 08:45:00"),
            ("ch_live_apex_904", "usr_apex_08", 3200.00, "FAILED", "Gateway processor timeout - Gateway dropped connection during settlement", "2026-10-26 06:10:00"),
            ("ch_live_apex_905", "usr_apex_09", 8500.00, "PAID", "Payment authorized and settled successfully", "2026-10-26 09:00:00")
        ]
        cur.executemany("INSERT INTO charges VALUES (?, ?, ?, ?, ?, ?);", charges_data)

        # Invoices table (2 severe overdue debt vulnerabilities + 1 paid baseline)
        cur.execute("""
        CREATE TABLE invoices (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT
        );
        """)
        invoices_data = [
            ("INV-ENT-2026-901", "usr_apex_03", 24850.00, "OVERDUE", (datetime.now(timezone.utc) - timedelta(days=68)).strftime("%Y-%m-%d")),
            ("INV-ENT-2026-902", "usr_apex_04", 12400.00, "OVERDUE", (datetime.now(timezone.utc) - timedelta(days=38)).strftime("%Y-%m-%d")),
            ("INV-ENT-2026-903", "usr_apex_10", 4200.00, "PAID", (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"))
        ]
        cur.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?);", invoices_data)

        # Carts table (2 high-intent abandoned checkout vulnerabilities)
        cur.execute("""
        CREATE TABLE carts (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            total REAL NOT NULL,
            status TEXT NOT NULL
        );
        """)
        carts_data = [
            ("chk_live_apex_801", "usr_apex_05", 5250.00, "ABANDONED"),
            ("chk_live_apex_802", "usr_apex_06", 2100.00, "ABANDONED")
        ]
        cur.executemany("INSERT INTO carts VALUES (?, ?, ?, ?);", carts_data)

        conn.commit()
        conn.close()

    # -------------------------------------------------------------
    # 2. GENERATE JSON EXPORT WITH DETAILED VULNERABILITY CONTEXT
    # -------------------------------------------------------------
    json_payload = {
        "organization": "Apex Global Enterprise Cloud Inc",
        "description": "Multi-tenant B2B Cloud Infrastructure & Cybersecurity Platform",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_revenue_at_risk_preview": "$74,050.00",
        "business_vulnerabilities_summary": [
            {
                "category": "RECURRING_SUBSCRIPTION_FREEZE",
                "severity": "CRITICAL",
                "vulnerability": "Expired corporate credit card for high-value Enterprise client ($14,500.00/mo). Zero retries executed due to missing automated dunning.",
                "affected_customer": "Nexus HealthTech Enterprise",
                "recommended_action": "Simulated card update dunning link with supervisor notification"
            },
            {
                "category": "PROCESSOR_VELOCITY_FALSE_POSITIVE",
                "severity": "HIGH",
                "vulnerability": "Legitimate mid-market account ($6,800.00) locked out by card network velocity rule false-positive.",
                "affected_customer": "CyberPulse Security Systems",
                "recommended_action": "Simulated smart-retry with 3DS challenge token after 24h cooldown"
            },
            {
                "category": "CRITICAL_AGING_ACCOUNTS_RECEIVABLE",
                "severity": "CRITICAL",
                "vulnerability": "Uncollected B2B invoice of $24,850.00 aging 68 days past Net-60 terms. Legacy billing email bounced.",
                "affected_customer": "Metropolis Infrastructure Group",
                "recommended_action": "Manual executive escalation & updated AP contact phone verification"
            },
            {
                "category": "MID_MARKET_TERMS_BREACH",
                "severity": "HIGH",
                "vulnerability": "Milestone invoice ($12,400.00) 38 days overdue awaiting vendor tax verification release.",
                "affected_customer": "Orbit Satellite Communications Ltd",
                "recommended_action": "Tax verification notice dispatch & accounts receivable phone outreach"
            },
            {
                "category": "ENTERPRISE_CART_ABANDONMENT",
                "severity": "HIGH",
                "vulnerability": "High-intent buyer abandoned $5,250.00 multi-node migration license 4h ago after 3DS challenge timeout.",
                "affected_customer": "Vanguard Aerospace Solutions",
                "recommended_action": "High-priority abandoned cart reminder with 1-click direct checkout link"
            },
            {
                "category": "SEAT_EXPANSION_TAX_CALCULATION_DROP",
                "severity": "MEDIUM",
                "vulnerability": "Existing paying customer dropped $2,100.00 team expansion cart at tax calculation step.",
                "affected_customer": "Synergy BioLabs",
                "recommended_action": "Assisted cart recovery notice with 10% annual expansion incentive"
            },
            {
                "category": "CROSS_BORDER_SETTLEMENT_BLOCK",
                "severity": "HIGH",
                "vulnerability": "European client ($4,950.00) recurring billing blocked by issuer cross-border restriction.",
                "affected_customer": "Solaria Energy International",
                "recommended_action": "Alternative SEPA/local payment method dispatch"
            },
            {
                "category": "GATEWAY_PROCESSOR_TIMEOUT",
                "severity": "MEDIUM",
                "vulnerability": "Payment of $3,200.00 timed out during gateway network spike. Never retried.",
                "affected_customer": "Hyperion Media Cloud",
                "recommended_action": "Safe idempotent gateway retry execution"
            }
        ],
        "customers": [
            {"id": "usr_apex_01", "name": "Nexus HealthTech Enterprise", "email": "billing@nexushealth.org", "phone": "+1-415-555-0144"},
            {"id": "usr_apex_02", "name": "CyberPulse Security Systems", "email": "devon@cyberpulse.net", "phone": "+1-312-555-0199"},
            {"id": "usr_apex_03", "name": "Metropolis Infrastructure Group", "email": "finance@metropolis-infrastructure.com", "phone": "+1-212-555-0112"},
            {"id": "usr_apex_04", "name": "Orbit Satellite Communications Ltd", "email": "accounts@orbitsat.co.uk", "phone": "+44-20-7946-0922"},
            {"id": "usr_apex_05", "name": "Vanguard Aerospace Solutions", "email": "procurement@vanguardaero.com", "phone": "+1-206-555-0187"},
            {"id": "usr_apex_06", "name": "Synergy BioLabs", "email": "elena.rostova@synergybiolabs.com", "phone": "+1-617-555-0131"},
            {"id": "usr_apex_07", "name": "Solaria Energy International", "email": "cfo@solariaenergy.eu", "phone": "+49-30-2312-5544"},
            {"id": "usr_apex_08", "name": "Hyperion Media Cloud", "email": "marcus@hyperionmedia.io", "phone": "+1-310-555-0165"}
        ],
        "transactions": [
            {
                "external_id": "ch_live_apex_901",
                "customer_id": "usr_apex_01",
                "amount": "14500.00",
                "currency": "USD",
                "status": "FAILED",
                "failure_code": "expired_card",
                "failure_reason": "Card expired or replaced by issuing bank - Zero retry attempts initiated (Silent recurring drop)"
            },
            {
                "external_id": "ch_live_apex_902",
                "customer_id": "usr_apex_02",
                "amount": "6800.00",
                "currency": "USD",
                "status": "FAILED",
                "failure_code": "velocity_exceeded",
                "failure_reason": "Processor velocity check exceeded - Network fraud rule false positive lockout"
            },
            {
                "external_id": "ch_live_apex_903",
                "customer_id": "usr_apex_07",
                "amount": "4950.00",
                "currency": "USD",
                "status": "FAILED",
                "failure_code": "cross_border_blocked",
                "failure_reason": "Cross-border transaction not permitted - Issuer foreign exchange settlement block"
            },
            {
                "external_id": "ch_live_apex_904",
                "customer_id": "usr_apex_08",
                "amount": "3200.00",
                "currency": "USD",
                "status": "FAILED",
                "failure_code": "gateway_timeout",
                "failure_reason": "Gateway processor timeout - Gateway dropped connection during settlement"
            }
        ],
        "invoices": [
            {
                "invoice_number": "INV-ENT-2026-901",
                "customer_id": "usr_apex_03",
                "amount": "24850.00",
                "currency": "USD",
                "status": "OVERDUE",
                "days_overdue": 68,
                "due_date": (datetime.now(timezone.utc) - timedelta(days=68)).strftime("%Y-%m-%d"),
                "notes": "Critical aging debt past Net-60 terms. Legacy billing email bounced."
            },
            {
                "invoice_number": "INV-ENT-2026-902",
                "customer_id": "usr_apex_04",
                "amount": "12400.00",
                "currency": "USD",
                "status": "OVERDUE",
                "days_overdue": 38,
                "due_date": (datetime.now(timezone.utc) - timedelta(days=38)).strftime("%Y-%m-%d"),
                "notes": "Milestone invoice awaiting vendor tax ID verification."
            }
        ],
        "checkouts": [
            {
                "checkout_token": "chk_live_apex_801",
                "customer_id": "usr_apex_05",
                "amount": "5250.00",
                "currency": "USD",
                "status": "ABANDONED",
                "cart_items_count": 50,
                "notes": "Enterprise Cloud Migration Pack abandoned after 3DS challenge timeout."
            },
            {
                "checkout_token": "chk_live_apex_802",
                "customer_id": "usr_apex_06",
                "amount": "2100.00",
                "currency": "USD",
                "status": "ABANDONED",
                "cart_items_count": 20,
                "notes": "20-Seat Team Analytics Expansion Module abandoned at tax step."
            }
        ]
    }

    for target_json in (json_vulnerabilities_path, json_default_path):
        with open(target_json, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2)

    print("Successfully generated datasets:")
    print(" - SQLite DB:", db_vulnerabilities_path)
    print(" - JSON Export:", json_vulnerabilities_path)

if __name__ == "__main__":
    generate_datasets()
