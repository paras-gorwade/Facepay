import sqlite3

from database.student_db import add_student


def main():
    print("\n--- FacePay Student Registration ---")

    student_id = input("Enter student ID: ").strip()
    name = input("Enter student name: ").strip()

    balance_input = input(
        "Enter initial wallet balance (default ₹500): "
    ).strip()

    try:
        initial_balance = (
            float(balance_input) if balance_input else 500.00
        )

        add_student(student_id, name, initial_balance)

    except (ValueError, sqlite3.IntegrityError) as error:
        print(f"Registration failed: {error}")


if __name__ == "__main__":
    main()

