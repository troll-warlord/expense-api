"""seed_test_data

Seeds three demo users with realistic transaction history.

Fully deterministic: uses a fixed random seed and a fixed reference date
(2026-02-23) so the generated data is identical on every run.

Safe to re-run: skips users and transactions that already exist (idempotent).

Demo logins (all use OTP 000000):
  +91 1111111111  — Arjun Sharma   (salary 65 000)
  +91 2222222222  — Priya Patel    (salary 85 000)
  +91 3333333333  — Ravi Kumar     (salary 55 000)

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:00:02.000000

"""

import random
import uuid as uuid_module
from collections.abc import Sequence
from datetime import date, timedelta

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ---------------------------------------------------------------------------
# Reference date — all transaction dates are relative to this fixed point
# so the generated data is the same regardless of when the migration runs.
# ---------------------------------------------------------------------------
REFERENCE_DATE = date(2026, 2, 23)

# (user_id, country_code, phone, first_name, last_name, monthly_salary, rng_seed)
DEMO_USERS = [
    ("c1000001-0000-0000-0000-000000000001", "+91", "1111111111", "Arjun", "Sharma", 65000, 1001),
    ("c1000001-0000-0000-0000-000000000002", "+91", "2222222222", "Priya", "Patel", 85000, 1002),
    ("c1000001-0000-0000-0000-000000000003", "+91", "3333333333", "Ravi", "Kumar", 55000, 1003),
]

# ---------------------------------------------------------------------------
# Category UUIDs (from migration 0002)
# ---------------------------------------------------------------------------
CAT = {
    "salary": "a1000001-0000-0000-0000-000000000001",
    "freelance": "a1000001-0000-0000-0000-000000000002",
    "investment": "a1000001-0000-0000-0000-000000000004",
    "other_income": "a1000001-0000-0000-0000-000000000007",
    "food": "a1000002-0000-0000-0000-000000000001",
    "groceries": "a1000002-0000-0000-0000-000000000002",
    "transport": "a1000002-0000-0000-0000-000000000003",
    "shopping": "a1000002-0000-0000-0000-000000000004",
    "entertainment": "a1000002-0000-0000-0000-000000000005",
    "health": "a1000002-0000-0000-0000-000000000006",
    "bills": "a1000002-0000-0000-0000-000000000007",
    "education": "a1000002-0000-0000-0000-000000000008",
    "travel": "a1000002-0000-0000-0000-000000000009",
    "personal_care": "a1000002-0000-0000-0000-000000000010",
    "home_rent": "a1000002-0000-0000-0000-000000000011",
    "insurance": "a1000002-0000-0000-0000-000000000012",
    "emi": "a1000002-0000-0000-0000-000000000013",
    "subscriptions": "a1000002-0000-0000-0000-000000000014",
    "other_expense": "a1000002-0000-0000-0000-000000000015",
}

# ---------------------------------------------------------------------------
# Payment method UUIDs (from migration 0002)
# ---------------------------------------------------------------------------
PM = {
    "cash": "b1000001-0000-0000-0000-000000000001",
    "upi": "b1000001-0000-0000-0000-000000000002",
    "credit_card": "b1000001-0000-0000-0000-000000000003",
    "debit_card": "b1000001-0000-0000-0000-000000000004",
    "net_banking": "b1000001-0000-0000-0000-000000000005",
    "wallet": "b1000001-0000-0000-0000-000000000006",
}

PM_WEIGHTS = {"upi": 40, "credit_card": 25, "debit_card": 15, "cash": 12, "net_banking": 5, "wallet": 3}

# ---------------------------------------------------------------------------
# Seed budgets — one realistic set per demo user
#   (user_id, budget_id, category_id_or_None, amount)
# ---------------------------------------------------------------------------
DEMO_BUDGETS = [
    # ── Arjun Sharma — 65 000 salary ──────────────────────────────────────────
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000001", None,                                        48000),
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000002", "a1000002-0000-0000-0000-000000000001", 5000),  # Food & Dining
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000003", "a1000002-0000-0000-0000-000000000002", 3000),  # Groceries
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000004", "a1000002-0000-0000-0000-000000000003", 2500),  # Transport
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000005", "a1000002-0000-0000-0000-000000000004", 4000),  # Shopping
    ("c1000001-0000-0000-0000-000000000001", "d1000001-0000-0000-0000-000000000006", "a1000002-0000-0000-0000-000000000007", 3500),  # Bills & Utilities
    # ── Priya Patel — 85 000 salary ───────────────────────────────────────────
    ("c1000001-0000-0000-0000-000000000002", "d1000001-0000-0000-0000-000000000007", None,                                        65000),
    ("c1000001-0000-0000-0000-000000000002", "d1000001-0000-0000-0000-000000000008", "a1000002-0000-0000-0000-000000000001", 7000),  # Food & Dining
    ("c1000001-0000-0000-0000-000000000002", "d1000001-0000-0000-0000-000000000009", "a1000002-0000-0000-0000-000000000004", 8000),  # Shopping
    ("c1000001-0000-0000-0000-000000000002", "d1000001-0000-0000-0000-000000000010", "a1000002-0000-0000-0000-000000000009", 10000), # Travel
    ("c1000001-0000-0000-0000-000000000002", "d1000001-0000-0000-0000-000000000011", "a1000002-0000-0000-0000-000000000007", 5000),  # Bills & Utilities
    # ── Ravi Kumar — 55 000 salary ────────────────────────────────────────────
    ("c1000001-0000-0000-0000-000000000003", "d1000001-0000-0000-0000-000000000012", None,                                        38000),
    ("c1000001-0000-0000-0000-000000000003", "d1000001-0000-0000-0000-000000000013", "a1000002-0000-0000-0000-000000000001", 3500),  # Food & Dining
    ("c1000001-0000-0000-0000-000000000003", "d1000001-0000-0000-0000-000000000014", "a1000002-0000-0000-0000-000000000002", 2500),  # Groceries
    ("c1000001-0000-0000-0000-000000000003", "d1000001-0000-0000-0000-000000000015", "a1000002-0000-0000-0000-000000000003", 2000),  # Transport
    ("c1000001-0000-0000-0000-000000000003", "d1000001-0000-0000-0000-000000000016", "a1000002-0000-0000-0000-000000000013", 10000), # EMI
]

# ---------------------------------------------------------------------------
# Transaction templates  (description, category_key, min_amount, max_amount)
# ---------------------------------------------------------------------------
EXPENSE_TEMPLATES = [
    ("Zomato order", "food", 150, 900),
    ("Swiggy order", "food", 120, 750),
    ("Restaurant dinner", "food", 400, 2500),
    ("Big Basket groceries", "groceries", 500, 3000),
    ("Kirana store", "groceries", 100, 800),
    ("Uber ride", "transport", 80, 600),
    ("Ola cab", "transport", 60, 500),
    ("Metro recharge", "transport", 50, 200),
    ("Petrol fill-up", "transport", 500, 2000),
    ("Amazon purchase", "shopping", 200, 4000),
    ("Myntra order", "shopping", 500, 3500),
    ("Netflix subscription", "subscriptions", 199, 199),
    ("Spotify premium", "subscriptions", 59, 59),
    ("Movie tickets", "entertainment", 300, 1200),
    ("Concert tickets", "entertainment", 800, 3000),
    ("Gym membership", "health", 500, 1500),
    ("Pharmacy", "health", 100, 800),
    ("Doctor consultation", "health", 300, 1500),
    ("Electricity bill", "bills", 800, 3000),
    ("Mobile recharge", "bills", 239, 599),
    ("Internet bill", "bills", 500, 1200),
    ("House rent", "home_rent", 8000, 20000),
    ("Online course", "education", 500, 5000),
    ("Books", "education", 200, 1000),
    ("Life insurance premium", "insurance", 1000, 5000),
    ("EMI payment", "emi", 2000, 15000),
    ("Hair salon", "personal_care", 200, 800),
    ("Flight ticket", "travel", 3000, 12000),
    ("Hotel stay", "travel", 1500, 8000),
]

INCOME_TEMPLATES = [
    ("Freelance project", "freelance", 5000, 25000),
    ("Dividend received", "investment", 1000, 8000),
    ("Cashback credit", "other_income", 50, 500),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_date(rng: random.Random, max_days_ago: int = 90) -> date:
    return REFERENCE_DATE - timedelta(days=rng.randint(0, max_days_ago))


def _weighted_pm(rng: random.Random) -> str:
    keys = list(PM_WEIGHTS.keys())
    wts = list(PM_WEIGHTS.values())
    return rng.choices(keys, weights=wts, k=1)[0]


def _build_transactions(user_id: str, salary: int, seed: int) -> list[dict]:
    """Generate a deterministic set of transactions for one user."""
    rng = random.Random(seed)
    rows: list[dict] = []

    # 38 random expense transactions spread over the last 90 days
    for desc, cat_k, low, high in rng.choices(EXPENSE_TEMPLATES, k=38):
        rows.append(
            {
                "id": str(uuid_module.UUID(int=rng.getrandbits(128))),
                "amount": rng.randint(low, high),
                "date": _random_date(rng),
                "description": desc,
                "category_id": CAT[cat_k],
                "payment_method_id": PM[_weighted_pm(rng)],
                "source": "mobile",
                "created_by": user_id,
                "updated_by": user_id,
            }
        )

    # 3 salary credits on the 1st of each of the last 3 months
    ref_first = REFERENCE_DATE.replace(day=1)
    for months_ago in [2, 1, 0]:
        salary_date = (ref_first - timedelta(days=months_ago * 30)).replace(day=1)
        rows.append(
            {
                "id": str(uuid_module.UUID(int=rng.getrandbits(128))),
                "amount": salary,
                "date": salary_date,
                "description": "Monthly salary credit",
                "category_id": CAT["salary"],
                "payment_method_id": PM["net_banking"],
                "source": "web",
                "created_by": user_id,
                "updated_by": user_id,
            }
        )

    # 5 misc income entries
    for desc, cat_k, low, high in rng.choices(INCOME_TEMPLATES, k=5):
        rows.append(
            {
                "id": str(uuid_module.UUID(int=rng.getrandbits(128))),
                "amount": rng.randint(low, high),
                "date": _random_date(rng),
                "description": desc,
                "category_id": CAT[cat_k],
                "payment_method_id": PM["upi"],
                "source": "web",
                "created_by": user_id,
                "updated_by": user_id,
            }
        )

    return rows


# ---------------------------------------------------------------------------


def upgrade() -> None:
    bind = op.get_bind()

    for user_id, country_code, phone, first_name, last_name, salary, seed in DEMO_USERS:
        # Insert user only if the phone number is not already registered
        bind.execute(
            sa.text(
                "INSERT INTO users"
                " (id, country_code, phone_number, first_name, last_name,"
                "  is_profile_complete, is_active, created_at, updated_at)"
                " SELECT :id, :cc, :phone, :first, :last, true, true, now(), now()"
                " WHERE NOT EXISTS ("
                "   SELECT 1 FROM users"
                "   WHERE country_code = :cc_chk AND phone_number = :phone_chk"
                " )"
            ),
            {
                "id": user_id,
                "cc": country_code,
                "phone": phone,
                "first": first_name,
                "last": last_name,
                "cc_chk": country_code,
                "phone_chk": phone,
            },
        )

        # Skip transaction seeding if this user already has transactions
        count = bind.execute(
            sa.text("SELECT COUNT(*) FROM transactions WHERE created_by = :uid"),
            {"uid": user_id},
        ).scalar()
        if count and count > 0:
            continue

        for row in _build_transactions(user_id, salary, seed):
            bind.execute(
                sa.text(
                    "INSERT INTO transactions"
                    " (id, amount, date, description, category_id, payment_method_id,"
                    "  source, created_at, updated_at, created_by, updated_by)"
                    " VALUES (:id, :amount, :date, :description, :category_id, :payment_method_id,"
                    "  :source, now(), now(), :created_by, :updated_by)"
                ),
                row,
            )

    # ── Seed budgets ─────────────────────────────────────────────────────────
    for user_id, budget_id, category_id, amount in DEMO_BUDGETS:
        bind.execute(
            sa.text(
                "INSERT INTO budgets"
                " (id, category_id, amount, period, created_at, updated_at, created_by, updated_by)"
                " VALUES (CAST(:id AS uuid), CAST(:category_id AS uuid), :amount, 'monthly',"
                "         now(), now(), CAST(:user_id AS uuid), CAST(:user_id AS uuid))"
                " ON CONFLICT DO NOTHING"
            ),
            {
                "id": budget_id,
                "category_id": category_id,
                "amount": amount,
                "user_id": user_id,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    user_ids = [row[0] for row in DEMO_USERS]
    placeholders = ", ".join(f":id{i}" for i in range(len(user_ids)))
    params = {f"id{i}": uid for i, uid in enumerate(user_ids)}
    bind.execute(sa.text(f"DELETE FROM budgets WHERE created_by IN ({placeholders})"), params)
    bind.execute(sa.text(f"DELETE FROM transactions WHERE created_by IN ({placeholders})"), params)
    bind.execute(sa.text(f"DELETE FROM users WHERE id IN ({placeholders})"), params)
