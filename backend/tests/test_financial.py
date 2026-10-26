import pytest
from backend.app.services.csv_importer import parse_amount_to_cents

def test_parse_amount_to_cents_standard():
    assert parse_amount_to_cents("149.99") == 14999
    assert parse_amount_to_cents("$149.99") == 14999
    assert parse_amount_to_cents("2500") == 250000
    assert parse_amount_to_cents("$2,500.00") == 250000
    assert parse_amount_to_cents("0.50") == 50
    assert parse_amount_to_cents("12.5") == 1250

def test_parse_amount_precision_no_float_drift():
    # Common float drift test: 0.1 + 0.2 != 0.3 in IEEE 754 float
    # In integer cents, 10 + 20 == 30 cents exactly
    c1 = parse_amount_to_cents("0.10")
    c2 = parse_amount_to_cents("0.20")
    assert c1 + c2 == 30
    assert f"${(c1 + c2) / 100:.2f}" == "$0.30"

def test_parse_amount_invalid_raises():
    with pytest.raises(ValueError):
        parse_amount_to_cents("invalid")
    with pytest.raises(ValueError):
        parse_amount_to_cents("")
    with pytest.raises(ValueError):
        parse_amount_to_cents("12.34.56")

def test_financial_accumulation_exactness():
    # Adding 100 items of $0.07 should be exactly $7.00 (700 cents)
    cents_list = [parse_amount_to_cents("0.07") for _ in range(100)]
    total_cents = sum(cents_list)
    assert total_cents == 700
    assert total_cents / 100 == 7.0
