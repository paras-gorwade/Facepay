"""Secure PIN storage and verification for the FacePay prototype."""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "facepay.db"
ITERATIONS = 310_000
MAX_ATTEMPTS = 3
LOCK_SECONDS = 60


def _connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_pin_table():
    """Create PIN storage table without modifying existing wallet tables."""
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS student_pins (
                student_id TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0
            )"""
        )


def has_pin(student_id):
    initialize_pin_table()
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM student_pins WHERE student_id = ?", (str(student_id),)
        ).fetchone()
    return row is not None


def _valid_pin(pin):
    return isinstance(pin, str) and pin.isdigit() and 4 <= len(pin) <= 6


def set_pin(student_id, pin):
    """Set a 4–6 digit PIN, storing only a salted PBKDF2 hash."""
    if not _valid_pin(pin):
        raise ValueError("PIN must contain 4 to 6 digits.")
    initialize_pin_table()
    salt = secrets.token_bytes(16)
    pin_hash = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, ITERATIONS)
    with _connect() as conn:
        conn.execute(
            """INSERT INTO student_pins
               (student_id, salt, pin_hash, failed_attempts, locked_until)
               VALUES (?, ?, ?, 0, 0)
               ON CONFLICT(student_id) DO UPDATE SET
                 salt = excluded.salt,
                 pin_hash = excluded.pin_hash,
                 failed_attempts = 0,
                 locked_until = 0""",
            (str(student_id), salt.hex(), pin_hash.hex()),
        )


def verify_pin(student_id, pin):
    """Return (success, message); lock out after 3 failures for 60 seconds."""
    initialize_pin_table()
    with _connect() as conn:
        row = conn.execute(
            """SELECT salt, pin_hash, failed_attempts, locked_until
               FROM student_pins WHERE student_id = ?""",
            (str(student_id),),
        ).fetchone()
        if row is None:
            return False, "No PIN is registered for this student."

        salt_hex, expected_hex, failures, locked_until = row
        now = time.time()
        if locked_until > now:
            return False, f"PIN locked. Try again in {int(locked_until - now) + 1} seconds."

        if not _valid_pin(pin):
            candidate = b""
        else:
            candidate = hashlib.pbkdf2_hmac(
                "sha256", pin.encode(), bytes.fromhex(salt_hex), ITERATIONS
            )

        if hmac.compare_digest(candidate.hex(), expected_hex):
            conn.execute(
                "UPDATE student_pins SET failed_attempts = 0, locked_until = 0 WHERE student_id = ?",
                (str(student_id),),
            )
            return True, "PIN verified."

        failures += 1
        if failures >= MAX_ATTEMPTS:
            conn.execute(
                "UPDATE student_pins SET failed_attempts = 0, locked_until = ? WHERE student_id = ?",
                (now + LOCK_SECONDS, str(student_id)),
            )
            return False, "Too many incorrect PIN attempts. Locked for 60 seconds."
        conn.execute(
            "UPDATE student_pins SET failed_attempts = ?, locked_until = 0 WHERE student_id = ?",
            (failures, str(student_id)),
        )
        return False, f"Incorrect PIN. {MAX_ATTEMPTS - failures} attempt(s) remaining."
