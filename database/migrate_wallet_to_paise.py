import sqlite3
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "facepay.db"
BACKUP_PATH = PROJECT_ROOT / "database" / "facepay_backup_before_day5.db"


def migrate_wallet_schema():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    # Preserve the original database before modifying its schema.
    if not BACKUP_PATH.exists():
        shutil.copy2(DATABASE_PATH, BACKUP_PATH)
        print(f"Database backup created: {BACKUP_PATH}")
    else:
        print(f"Existing backup preserved: {BACKUP_PATH}")

    connection = sqlite3.connect(DATABASE_PATH, timeout=10)

    try:
        connection.execute("BEGIN IMMEDIATE")

        student_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        }

        transaction_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(transactions)"
            ).fetchall()
        }

        if "balance" not in student_columns:
            raise RuntimeError(
                "Expected students.balance column was not found."
            )

        if "amount" not in transaction_columns:
            raise RuntimeError(
                "Expected transactions.amount column was not found."
            )

        # Add integer-paise columns if this migration has not run.
        if "balance_paise" not in student_columns:
            connection.execute(
                "ALTER TABLE students "
                "ADD COLUMN balance_paise INTEGER"
            )

        if "amount_paise" not in transaction_columns:
            connection.execute(
                "ALTER TABLE transactions "
                "ADD COLUMN amount_paise INTEGER"
            )

        # Convert existing rupee values to integer paise.
        connection.execute("""
            UPDATE students
            SET balance_paise = CAST(
                ROUND(balance * 100) AS INTEGER
            )
            WHERE balance_paise IS NULL
        """)

        connection.execute("""
            UPDATE transactions
            SET amount_paise = CAST(
                ROUND(amount * 100) AS INTEGER
            )
            WHERE amount_paise IS NULL
        """)

        # Validate migrated values before committing.
        invalid_students = connection.execute("""
            SELECT student_id, balance
            FROM students
            WHERE balance_paise IS NULL
               OR balance_paise < 0
               OR ABS(balance * 100 - balance_paise) > 0.000001
        """).fetchall()

        invalid_transactions = connection.execute("""
            SELECT transaction_id, amount
            FROM transactions
            WHERE amount_paise IS NULL
               OR amount_paise <= 0
               OR ABS(amount * 100 - amount_paise) > 0.000001
        """).fetchall()

        if invalid_students or invalid_transactions:
            raise RuntimeError(
                "Migration validation failed. "
                f"Invalid students: {invalid_students}; "
                f"invalid transactions: {invalid_transactions}"
            )

        connection.commit()

        print("Wallet migration completed successfully.")
        print("Existing student records preserved.")
        print("Integer-paise columns are ready.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_wallet_schema()