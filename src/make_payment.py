from decimal import Decimal, InvalidOperation

from database.payment_service import (
    process_payment,
    PaymentError,
)


def main():
    print("\n========== FacePay Payment ==========")

    student_id = input("Enter student ID: ").strip()
    amount_input = input("Enter payment amount (INR): ").strip()

    if not student_id:
        print("Payment failed: Student ID cannot be empty.")
        return

    try:
        amount = Decimal(amount_input)

        result = process_payment(student_id, amount)

        print("\n========== PAYMENT SUCCESSFUL ==========")
        print(f"Transaction ID: {result['transaction_id']}")
        print(f"Student ID: {result['student_id']}")
        print(
            f"Amount: Rs. {result['amount_paise'] / 100:.2f}"
        )
        print(
            "Previous balance: Rs. "
            f"{result['previous_balance_paise'] / 100:.2f}"
        )
        print(
            "Updated balance: Rs. "
            f"{result['new_balance_paise'] / 100:.2f}"
        )

    except (InvalidOperation, ValueError, PaymentError) as error:
        print(f"\nPayment failed: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")


if __name__ == "__main__":
    main()