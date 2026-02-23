"""master_data

Inserts system-default categories and payment methods (is_default=True).
Uses INSERT ... SELECT WHERE NOT EXISTS so it is safe to re-run on a
database that already contains these rows (idempotent).

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:01.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ---------------------------------------------------------------------------
# Reference data — fixed UUIDs so this migration is fully deterministic
# ---------------------------------------------------------------------------

DEFAULT_CATEGORIES = [
    # income
    ("a1000001-0000-0000-0000-000000000001", "Salary", "income"),
    ("a1000001-0000-0000-0000-000000000002", "Freelance", "income"),
    ("a1000001-0000-0000-0000-000000000003", "Business Income", "income"),
    ("a1000001-0000-0000-0000-000000000004", "Investment", "income"),
    ("a1000001-0000-0000-0000-000000000005", "Rental Income", "income"),
    ("a1000001-0000-0000-0000-000000000006", "Gift Received", "income"),
    ("a1000001-0000-0000-0000-000000000007", "Other Income", "income"),
    # expense
    ("a1000002-0000-0000-0000-000000000001", "Food & Dining", "expense"),
    ("a1000002-0000-0000-0000-000000000002", "Groceries", "expense"),
    ("a1000002-0000-0000-0000-000000000003", "Transport", "expense"),
    ("a1000002-0000-0000-0000-000000000004", "Shopping", "expense"),
    ("a1000002-0000-0000-0000-000000000005", "Entertainment", "expense"),
    ("a1000002-0000-0000-0000-000000000006", "Health & Fitness", "expense"),
    ("a1000002-0000-0000-0000-000000000007", "Bills & Utilities", "expense"),
    ("a1000002-0000-0000-0000-000000000008", "Education", "expense"),
    ("a1000002-0000-0000-0000-000000000009", "Travel", "expense"),
    ("a1000002-0000-0000-0000-000000000010", "Personal Care", "expense"),
    ("a1000002-0000-0000-0000-000000000011", "Home & Rent", "expense"),
    ("a1000002-0000-0000-0000-000000000012", "Insurance", "expense"),
    ("a1000002-0000-0000-0000-000000000013", "EMI / Loan", "expense"),
    ("a1000002-0000-0000-0000-000000000014", "Subscriptions", "expense"),
    ("a1000002-0000-0000-0000-000000000015", "Other Expense", "expense"),
]

DEFAULT_PAYMENT_METHODS = [
    ("b1000001-0000-0000-0000-000000000001", "Cash"),
    ("b1000001-0000-0000-0000-000000000002", "UPI"),
    ("b1000001-0000-0000-0000-000000000003", "Credit Card"),
    ("b1000001-0000-0000-0000-000000000004", "Debit Card"),
    ("b1000001-0000-0000-0000-000000000005", "Net Banking"),
    ("b1000001-0000-0000-0000-000000000006", "Wallet"),
    ("b1000001-0000-0000-0000-000000000007", "Cheque"),
    ("b1000001-0000-0000-0000-000000000008", "NEFT / RTGS"),
]

# ---------------------------------------------------------------------------


def upgrade() -> None:
    bind = op.get_bind()

    # Use INSERT ... SELECT WHERE NOT EXISTS so the migration is idempotent even
    # if rows with those names already exist.
    # Unique param names per clause avoid asyncpg type-inference conflicts.
    for id_, name, type_ in DEFAULT_CATEGORIES:
        bind.execute(
            sa.text(
                "INSERT INTO categories (id, name, type, is_default, created_at, updated_at)"
                " SELECT :id, :name_ins, :type_ins, true, now(), now()"
                " WHERE NOT EXISTS ("
                "   SELECT 1 FROM categories"
                "   WHERE name = :name_chk AND type = :type_chk AND is_default = true"
                " )"
            ),
            {"id": id_, "name_ins": name, "type_ins": type_, "name_chk": name, "type_chk": type_},
        )

    for id_, name in DEFAULT_PAYMENT_METHODS:
        bind.execute(
            sa.text(
                "INSERT INTO payment_methods (id, name, is_default, created_at, updated_at)"
                " SELECT :id, :name_ins, true, now(), now()"
                " WHERE NOT EXISTS ("
                "   SELECT 1 FROM payment_methods"
                "   WHERE name = :name_chk AND is_default = true"
                " )"
            ),
            {"id": id_, "name_ins": name, "name_chk": name},
        )


def downgrade() -> None:
    bind = op.get_bind()
    ids = [row[0] for row in DEFAULT_CATEGORIES]
    if ids:
        bind.execute(
            sa.text("DELETE FROM categories WHERE id = ANY(:ids)"),
            {"ids": ids},
        )
    ids = [row[0] for row in DEFAULT_PAYMENT_METHODS]
    if ids:
        bind.execute(
            sa.text("DELETE FROM payment_methods WHERE id = ANY(:ids)"),
            {"ids": ids},
        )
