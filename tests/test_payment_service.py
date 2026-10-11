import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from database.payment_service import (
    amount_to_paise,
    process_payment,
    get_wallet_balance_paise,
    InvalidAmountError,
    InsufficientBalanceError,
    StudentNotFoundError,
)


class TestPaymentService(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary database for each test.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_facepay.db"

        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE students (
                        student_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        balance REAL NOT NULL CHECK (balance >= 0),
                        balance_paise INTEGER NOT NULL
                    )
                """)

                connection.execute("""
                    CREATE TABLE transactions (
                        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        transaction_type TEXT NOT NULL,
                        amount_paise INTEGER NOT NULL,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id)
                            REFERENCES students(student_id)
                    )
                """)

                connection.execute("""
                    INSERT INTO students (
                        student_id,
                        name,
                        balance,
                        balance_paise
                    )
                    VALUES (?, ?, ?, ?)
                """, ("STU001", "paras", 500.00, 50000))

        # Direct payment-service database operations to the test database.
        self.patcher = patch(
            "database.payment_service.DATABASE_PATH",
            self.db_path,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    # Test 1: Rupees to paise conversion.
    def test_amount_conversion(self):
        self.assertEqual(amount_to_paise("50.25"), 5025)

    # Test 2: Reject zero payments.
    def test_reject_zero_payment(self):
        with self.assertRaises(InvalidAmountError):
            amount_to_paise("0")

    # Test 3: Reject negative payments.
    def test_reject_negative_payment(self):
        with self.assertRaises(InvalidAmountError):
            amount_to_paise("-10")

    # Test 4: Reject fractions of a paise.
    def test_reject_fraction_of_paise(self):
        with self.assertRaises(InvalidAmountError):
            amount_to_paise("10.001")

    # Test 5: Successful payment and transaction recording.
    def test_successful_payment(self):
        result = process_payment("STU001", "50")

        self.assertEqual(result["amount_paise"], 5000)
        self.assertEqual(result["previous_balance_paise"], 50000)
        self.assertEqual(result["new_balance_paise"], 45000)

        self.assertEqual(
            get_wallet_balance_paise("STU001"),
            45000,
        )

        with closing(sqlite3.connect(self.db_path)) as connection:
            transaction = connection.execute("""
                SELECT student_id, amount_paise, transaction_type
                FROM transactions
                WHERE transaction_id = ?
            """, (result["transaction_id"],)).fetchone()

        self.assertEqual(
            transaction,
            ("STU001", 5000, "debit"),
        )

    # Test 6: Insufficient funds must not deduct money.
    def test_insufficient_balance_does_not_deduct(self):
        with self.assertRaises(InsufficientBalanceError):
            process_payment("STU001", "600")

        self.assertEqual(
            get_wallet_balance_paise("STU001"),
            50000,
        )

        with closing(sqlite3.connect(self.db_path)) as connection:
            transaction_count = connection.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]

        self.assertEqual(transaction_count, 0)

    # Test 7: Missing student must be rejected.
    def test_missing_student(self):
        with self.assertRaises(StudentNotFoundError):
            process_payment("STU999", "10")

    # Test 8: Failed transaction insertion must roll back the payment.
    def test_transaction_insert_failure_rolls_back_payment(self):

        # Simulate a database failure during transaction insertion.
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("""
                CREATE TRIGGER fail_transaction_insert
                BEFORE INSERT ON transactions
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'Simulated transaction insertion failure'
                    );
                END;
            """)

        # The payment must fail when the transaction cannot be recorded.
        with self.assertRaises(sqlite3.IntegrityError):
            process_payment("STU001", "50")

        # The wallet balance must remain unchanged.
        self.assertEqual(
            get_wallet_balance_paise("STU001"),
            50000,
        )

        # No transaction should have been committed.
        with closing(sqlite3.connect(self.db_path)) as connection:
            transaction_count = connection.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]

        self.assertEqual(transaction_count, 0)

    def test_concurrent_payments_do_not_overspend(self):
        from concurrent.futures import ThreadPoolExecutor

        # Starting balance: ₹500.
        # Two simultaneous payments of ₹300 must not both succeed.
        def attempt_payment():
            try:
                process_payment("STU001", "300")
                return "success"
            except InsufficientBalanceError:
                return "insufficient_balance"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda _: attempt_payment(),
                    range(2),
                )
            )

        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("insufficient_balance"), 1)

        # Only ₹300 should have been deducted.
        self.assertEqual(
            get_wallet_balance_paise("STU001"),
            20000,
        )

        # Exactly one transaction should exist.
        with closing(sqlite3.connect(self.db_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()