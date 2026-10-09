from database.db_setup import get_connection, initialize_database


def add_student(student_id, name, initial_balance=500.00):
    """Add a student with an initial wallet balance."""
    if not student_id or not student_id.strip():
        raise ValueError("Student ID cannot be empty.")

    if not name or not name.strip():
        raise ValueError("Student name cannot be empty.")

    if initial_balance < 0:
        raise ValueError("Initial balance cannot be negative.")

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO students (student_id, name, balance)
            VALUES (?, ?, ?)
            """,
            (student_id.strip(), name.strip(), initial_balance),
        )

        print(f"Student added successfully: {name.strip()}")
        return cursor.rowcount


def get_student(student_id):
    """Retrieve a student by their unique ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT student_id, name, balance, created_at
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "student_id": row[0],
        "name": row[1],
        "balance": row[2],
        "created_at": row[3],
    }


def get_wallet_balance(student_id):
    """Return a student's wallet balance, or None if not found."""
    student = get_student(student_id)

    if student is None:
        return None

    return student["balance"]

