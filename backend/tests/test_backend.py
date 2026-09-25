"""Backend test suite covering auth, isolation, CRUD, budgets, CSV parsing,
duplicate detection, and the forecast API."""
import datetime
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app

SECRET = "local-test-secret-for-dev-only"


def make_token(user_id: str, email: str = "test@example.com") -> str:
    return jwt.encode(
        {"sub": user_id, "email": email, "aud": "authenticated",
         "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
        SECRET, algorithm="HS256",
    )


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {make_token('pytest-user-1')}"}


@pytest.fixture
def other_auth_headers():
    return {"Authorization": f"Bearer {make_token('pytest-user-2', email='other@example.com')}"}


def test_unauthenticated_request_rejected(client):
    r = client.get("/api/transactions")
    assert r.status_code == 401


def test_new_account_starts_empty(client, auth_headers):
    client.post("/api/profile", json={"full_name": "A", "user_type": "student"}, headers=auth_headers)
    r = client.get("/api/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_income"] == 0
    assert body["total_expenses"] == 0


def test_transaction_crud(client, auth_headers):
    r = client.post("/api/transactions", json={
        "date": "2026-01-01", "transaction_type": "expense", "amount": 100, "merchant": "Test Store",
    }, headers=auth_headers)
    assert r.status_code == 201
    txn_id = r.json()["transaction_id"]

    r = client.get(f"/api/transactions/{txn_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["amount"] == 100

    r = client.put(f"/api/transactions/{txn_id}", json={"amount": 200}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["amount"] == 200

    r = client.delete(f"/api/transactions/{txn_id}", headers=auth_headers)
    assert r.status_code == 204

    r = client.get(f"/api/transactions/{txn_id}", headers=auth_headers)
    assert r.status_code == 404  # soft-deleted, no longer visible


def test_user_data_isolation(client, auth_headers, other_auth_headers):
    r = client.post("/api/transactions", json={
        "date": "2026-01-01", "transaction_type": "expense", "amount": 500, "merchant": "Private Store",
    }, headers=auth_headers)
    txn_id = r.json()["transaction_id"]

    # user 2 must not be able to see user 1's transaction
    r = client.get(f"/api/transactions/{txn_id}", headers=other_auth_headers)
    assert r.status_code == 404

    r = client.get("/api/transactions", headers=other_auth_headers)
    assert all(t["transaction_id"] != txn_id for t in r.json()["items"])


def test_budget_progress_calculation(client, auth_headers):
    cats = client.get("/api/categories", headers=auth_headers).json()
    food_cat = next(c for c in cats if c["name"] == "Food")

    r = client.post("/api/budgets", json={
        "category_id": food_cat["id"], "name": "Food Budget",
        "period_month": 1, "period_year": 2026, "limit_amount": 1000,
    }, headers=auth_headers)
    budget_id = r.json()["id"]

    client.post("/api/transactions", json={
        "date": "2026-01-05", "transaction_type": "expense", "amount": 600,
        "category_id": food_cat["id"], "merchant": "Restaurant",
    }, headers=auth_headers)

    r = client.get(f"/api/budgets/{budget_id}/progress", headers=auth_headers)
    body = r.json()
    assert body["spent_amount"] == 600
    assert body["remaining_amount"] == 400
    assert body["warning_level"] == "50"


def test_csv_import_column_mapping_and_duplicate_detection(client, auth_headers):
    csv_content = (
        "Transaction Date,Narration,Withdrawal Amt,Deposit Amt\n"
        "01/02/2026,Swiggy Order,300.00,\n"
        "02/02/2026,Salary Credit,,50000.00\n"
    )
    files = {"file": ("bank.csv", csv_content.encode(), "text/csv")}
    r = client.post("/api/imports/csv/upload", files=files, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["suggested_mapping"]["debit_column"] == "Withdrawal Amt"
    assert body["preview_rows"][0]["parsed_type"] == "expense"
    assert body["preview_rows"][1]["parsed_type"] == "income"

    # re-upload identical file: rows should now be flagged duplicate only
    # after the first import is confirmed, so first upload shouldn't be
    # flagged against itself
    assert body["duplicate_rows"] == 0


def test_forecast_insufficient_data_for_new_user(client, auth_headers):
    r = client.post("/api/forecasts/generate", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["confidence_level"] == "insufficient_data"


def test_model_status_endpoint(client):
    r = client.get("/api/forecasts/model-status")
    assert r.status_code == 200
    body = r.json()
    assert body["model_available"] is True
    assert body["test_mae"] is not None


def test_investment_tracking(client, auth_headers):
    r = client.post("/api/investments", json={
        "investment_name": "Test Fund", "investment_type": "mutual_fund",
        "amount_invested": 10000, "investment_date": "2026-01-01",
    }, headers=auth_headers)
    assert r.status_code == 201

    r = client.get("/api/investments", headers=auth_headers)
    assert len(r.json()) >= 1


def test_savings_goal_contribution_progress(client, auth_headers):
    r = client.post("/api/goals", json={
        "goal_name": "Bike", "target_amount": 50000, "target_date": "2027-01-01",
    }, headers=auth_headers)
    goal_id = r.json()["goal_id"]

    r = client.post(f"/api/goals/{goal_id}/contributions", json={
        "amount": 10000, "contribution_date": "2026-01-01",
    }, headers=auth_headers)
    assert r.status_code == 201

    r = client.get("/api/goals", headers=auth_headers)
    goal = next(g for g in r.json() if g["goal_id"] == goal_id)
    assert goal["current_amount"] == 10000
