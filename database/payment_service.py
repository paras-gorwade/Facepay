import sqlite3
from contextlib import closing
from decimal import Decimal, InvalidOperation

from database.db_setup import DATABASE_PATH  # tests patch this name


class InvalidAmountError(ValueError):
    """Raised when a payment amount is invalid."""


class InsufficientBalanceError(Exception):
    """Raised when the wallet balance is too low."""


class StudentNotFoundError(Exception):
    """Raised when the student does not exist."""

class PaymentError(Exception):
    """Base exception for payment failures."""


class InvalidAmountError(PaymentError):
    """Raised when a payment amount is invalid."""


class InsufficientBalanceError(PaymentError):
    """Raised when the wallet balance is too low."""


class StudentNotFoundError(PaymentError):
    """Raised when the student does not exist."""


def _connect():
    # Looked up at call time, so patching DATABASE_PATH in tests works
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def amount_to_paise(amount):
    """Convert a rupee amount (e.g. '50.25') to integer paise."""
    try:
        value = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError):
        raise InvalidAmountError("Amount must be a valid number.")

    if not value.is_finite():
        raise InvalidAmountError("Amount must be a valid number.")

    if value <= 0:
        raise InvalidAmountError("Amount must be greater than zero.")

    paise = value * 100
    if paise != paise.to_integral_value():
        raise InvalidAmountError("Amount cannot have fractions of a paisa.")

    return int(paise)


def get_wallet_balance_paise(student_id):
    """Return the student's balance in paise."""
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT balance_paise FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()

    if row is None:
        raise StudentNotFoundError(f"Student not found: {student_id}")

    return row[0]


def process_payment(student_id, amount):
    """Deduct a payment and record it, atomically."""
    amount_paise = amount_to_paise(amount)

    with closing(_connect()) as connection:
        with connection:  # commit on success, roll back on any exception
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                "SELECT balance_paise FROM students WHERE student_id = ?",
                (student_id,),
            ).fetchone()

            if row is None:
                raise StudentNotFoundError(f"Student not found: {student_id}")

            previous = row[0]
            if previous < amount_paise:
                raise InsufficientBalanceError("Insufficient wallet balance.")

            new_balance = previous - amount_paise

            connection.execute(
                """
                UPDATE students
                SET balance_paise = ?, balance = ?
                WHERE student_id = ?
                """,
                (new_balance, new_balance / 100, student_id),
            )

            cursor = connection.execute(
                """
                INSERT INTO transactions
                    (student_id, amount, transaction_type, amount_paise)
                VALUES (?, ?, 'debit', ?)
                """,
                (student_id, amount_paise / 100, amount_paise),
            )
            transaction_id = cursor.lastrowid

    return {
        "transaction_id": transaction_id,
        "student_id": student_id,
        "amount_paise": amount_paise,
        "previous_balance_paise": previous,
        "new_balance_paise": new_balance,
    }