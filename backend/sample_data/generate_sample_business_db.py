import sqlite3
import json
import os

os.makedirs("backend/sample_data", exist_ok=True)
db_path = "backend/sample_data/real_business_database.db"
json_path = "backend/sample_data/business_export.json"

if os.path.exists(db_path):
    os.remove(db_path)

# 1. Create SQLite business database
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Customers/Users
cur.execute("""
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT
);
""")
users_data = [
    ("usr_atlas_01", "Nexus Cloud Corp (Marcus Vance)", "marcus@nexuscloud.io", "+1-415-555-0192"),
    ("usr_vortex_02", "Apex Retail Holdings (Elena Rostova)", "elena@apexholdings.com", "+1-212-555-0143"),
    ("usr_lumina_03", "Hyperion BioLabs (Dr. Aris Thorne)", "athorne@hyperionbiolabs.org", "+1-617-555-0188"),
    ("usr_solaris_04", "Velocity Logistics Ltd (Kavita Sharma)", "kavita@velocitylog.co.uk", "+44-20-7946-0912"),
    ("usr_zenith_05", "CyberPulse Security (Devon Reed)", "devon@cyberpulse.net", "+1-312-555-0176")
]
cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?);", users_data)

# Payment charges (with real gateway decline abnormalities)
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
    ("ch_live_9011", "usr_atlas_01", 3450.00, "FAILED", "Card velocity check exceeded - Do Not Honor", "2026-10-24 14:22:00"),
    ("ch_live_9012", "usr_lumina_03", 1820.50, "FAILED", "Card expired or replaced by issuing bank", "2026-10-25 09:10:00"),
    ("ch_live_9013", "usr_zenith_05", 940.00, "FAILED", "Insufficient available funds on corporate card", "2026-10-25 18:45:00"),
    ("ch_live_9014", "usr_atlas_01", 5200.00, "FAILED", "Generic processor decline - SCA challenge failed", "2026-10-26 04:30:00")
]
cur.executemany("INSERT INTO charges VALUES (?, ?, ?, ?, ?, ?);", charges_data)

# Invoices (with aging debt abnormalities)
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
    ("INV-LIVE-8801", "usr_vortex_02", 8750.00, "OVERDUE", "2026-09-15"),
    ("INV-LIVE-8802", "usr_solaris_04", 4320.00, "OVERDUE", "2026-10-01"),
    ("INV-LIVE-8803", "usr_lumina_03", 2600.00, "OVERDUE", "2026-10-05")
]
cur.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?);", invoices_data)

# Abandoned Checkouts (high-intent dropped sales)
cur.execute("""
CREATE TABLE carts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    total REAL NOT NULL,
    status TEXT NOT NULL
);
""")
carts_data = [
    ("chk_live_cart_01", "usr_zenith_05", 1490.00, "ABANDONED"),
    ("chk_live_cart_02", "usr_atlas_01", 850.00, "ABANDONED"),
    ("chk_live_cart_03", "usr_vortex_02", 2150.00, "ABANDONED")
]
cur.executemany("INSERT INTO carts VALUES (?, ?, ?, ?);", carts_data)

conn.commit()
conn.close()
print("Sample real SQLite database created at:", db_path)

# 2. Create sample JSON export
json_payload = {
    "organization": "Enterprise Global Business Corp",
    "export_timestamp": "2026-10-26T10:00:00Z",
    "customers": [
        {"id": "c_json_01", "name": "Quantum Leap Robotics", "email": "billing@quantumleap.ai", "phone": "+1-415-555-8921"},
        {"id": "c_json_02", "name": "BioHealth Global Systems", "email": "finance@biohealth.org", "phone": "+1-650-555-4309"},
        {"id": "c_json_03", "name": "Aether Dynamics Space Inc", "email": "pay@aetherdynamics.com", "phone": "+1-310-555-7711"}
    ],
    "transactions": [
        {"external_id": "tx_stripe_9901", "customer_id": "c_json_01", "amount": "4500.00", "status": "FAILED", "failure_code": "card_declined", "failure_reason": "Processor decline: suspected fraud rule blocked card", "currency": "USD"},
        {"external_id": "tx_stripe_9902", "customer_id": "c_json_02", "amount": "1950.00", "status": "FAILED", "failure_code": "insufficient_funds", "failure_reason": "Insufficient account balance on recurring billing cycle", "currency": "USD"}
    ],
    "invoices": [
        {"invoice_number": "INV-ENT-2026-44", "customer_id": "c_json_03", "amount": "9200.00", "status": "OVERDUE", "days_overdue": 34, "currency": "USD"},
        {"invoice_number": "INV-ENT-2026-45", "customer_id": "c_json_01", "amount": "3100.00", "status": "OVERDUE", "days_overdue": 18, "currency": "USD"}
    ],
    "checkouts": [
        {"checkout_token": "chk_shop_8891", "customer_id": "c_json_02", "amount": "1250.00", "cart_items_count": 3, "status": "ABANDONED", "currency": "USD"},
        {"checkout_token": "chk_shop_8892", "customer_id": "c_json_03", "amount": "890.00", "cart_items_count": 1, "status": "ABANDONED", "currency": "USD"}
    ]
}

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_payload, f, indent=2)

print("Sample real JSON business export created at:", json_path)
