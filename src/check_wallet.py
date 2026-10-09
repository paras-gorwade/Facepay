from database.student_db import get_student


def main():
    print("\n--- FacePay Wallet Lookup ---")

    student_id = input("Enter student ID: ").strip()
    student = get_student(student_id)

    if student is None:
        print("Student not found.")
        return

    print("\nStudent Details")
    print("-------------------------")
    print(f"Student ID: {student['student_id']}")
    print(f"Name: {student['name']}")
    print(f"Wallet Balance: ₹{student['balance']:.2f}")
    print(f"Created At: {student['created_at']}")


if __name__ == "__main__":
    main()

