import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from database.student_db import get_student, get_wallet_balance


class TestStudentDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_facepay.db"
        self._connections = []  # track every connection we hand out

        # closing() actually closes the connection; "with connection" does not
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:  # commits the transaction
                connection.execute("""
                    CREATE TABLE students (
                        student_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        balance REAL NOT NULL CHECK (balance >= 0),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                connection.executemany(
                    """
                    INSERT INTO students (student_id, name, balance)
                    VALUES (?, ?, ?)
                    """,
                    [
                        ("STU001", "paras", 500.00),
                        ("STU002", "rohan", 300.00),
                    ],
                )

        self.connection_patcher = patch(
            "database.student_db.get_connection",
            side_effect=self.get_test_connection,
        )
        self.connection_patcher.start()

    def get_test_connection(self):
        connection = sqlite3.connect(self.db_path)
        self._connections.append(connection)
        return connection

    def tearDown(self):
        self.connection_patcher.stop()

        # Close any connection the code under test left open
        for connection in self._connections:
            try:
                connection.close()
            except sqlite3.Error:
                pass

        self.temp_dir.cleanup()

    def test_get_existing_student(self):
        student = get_student("STU001")

        self.assertIsNotNone(student)
        self.assertEqual(student["student_id"], "STU001")
        self.assertEqual(student["name"], "paras")
        self.assertAlmostEqual(student["balance"], 500.00)

    def test_get_missing_student(self):
        student = get_student("STU999")

        self.assertIsNone(student)

    def test_get_existing_wallet_balance(self):
        balance = get_wallet_balance("STU001")

        self.assertAlmostEqual(balance, 500.00)

    def test_get_missing_wallet_balance(self):
        balance = get_wallet_balance("STU999")

        self.assertIsNone(balance)


if __name__ == "__main__":
    unittest.main()