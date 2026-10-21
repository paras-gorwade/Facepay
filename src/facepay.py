import os
import time

import cv2
import face_recognition

from database.payment_service import (
    amount_to_paise,
    process_payment,
    get_wallet_balance_paise,
    InvalidAmountError,
    InsufficientBalanceError,
    StudentNotFoundError,
)
from src.recognition import load_encodings, load_student_cache, recognize_student
from src.gesture_confirmation import GestureConfirmation
from database.pin_service import has_pin, set_pin, verify_pin
from getpass import getpass

SCALE = 0.5
DETECT_EVERY = 2
STABLE_CYCLES = 3
CONFIRM_TIMEOUT = 20  # seconds allowed for a fresh thumbs-up


def rs(paise):
    return f"Rs. {paise / 100:.2f}"


def put_text(frame, text, pos, color, scale=0.6):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)


def open_camera():
    # DirectShow opens faster and more reliably on Windows
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
    if not camera.isOpened():
        camera.release()
        return None
    return camera


def draw_faces(frame, faces):
    for (top, right, bottom, left), name, student in faces:
        if student:
            label, color = f"{student['name']} | {student['student_id']}", (0, 255, 0)
            put_text(frame, f"Wallet: Rs. {student['balance']:.2f}", (left, bottom + 25), color)
        elif name:
            label, color = f"{name} | No database record", (0, 165, 255)
        else:
            label, color = "Unknown", (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        put_text(frame, label, (left, max(top - 10, 25)), color)


class FacePayApp:
    def __init__(self, camera, known_encodings, known_names, student_cache):
        self.camera = camera
        self.known_encodings = known_encodings
        self.known_names = known_names
        self.student_cache = student_cache

    def find_faces(self, frame):
        # match on a smaller frame for speed, then scale boxes back up
        small = cv2.resize(frame, (0, 0), fx=SCALE, fy=SCALE)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        faces = []
        for encoding, location in zip(encodings, locations):
            name = recognize_student(encoding, self.known_encodings, self.known_names)
            student = self.student_cache.get(name.strip().casefold()) if name else None
            box = tuple(int(v / SCALE) for v in location)
            faces.append((box, name, student))
        return faces

    def refresh_cache(self):
        # reload so the on-screen wallet balance is never stale
        try:
            self.student_cache = load_student_cache()
        except Exception as error:
            print(f"Warning: could not refresh student records: {error}")

    def recognize_live(self):
        print("\n--- FacePay Recognition ---")
        print("Look at the camera. Press P to initiate payment, Q to exit.")

        faces, count, last_id, streak = [], 0, None, 0

        try:
            while True:
                success, frame = self.camera.read()
                if not success:
                    print("Error: Could not read webcam frame.")
                    return None

                # heavy face matching only every few frames
                if count % DETECT_EVERY == 0:
                    faces = self.find_faces(frame)
                    students = [s for _, _, s in faces if s]

                    if len(faces) == 1 and students:
                        # the same student must stay recognized across several cycles
                        streak = streak + 1 if students[0]["student_id"] == last_id else 1
                        last_id = students[0]["student_id"]
                    else:
                        streak, last_id = 0, None
                count += 1

                draw_faces(frame, faces)
                ready = streak >= STABLE_CYCLES

                if ready:
                    put_text(frame, "Press P to initiate payment", (20, 70), (255, 255, 0), 0.65)
                elif streak > 0:
                    put_text(frame, "Recognizing...", (20, 70), (0, 255, 255), 0.65)
                else:
                    put_text(frame, "Show one registered student", (20, 70), (0, 165, 255), 0.65)

                cv2.imshow("FacePay - Student Recognition", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    return None
                if key == ord("p") and ready:
                    return faces[0][2].copy()
        finally:
            cv2.destroyAllWindows()

    @staticmethod
    def reset_gesture_state(detector):
        detector.history.clear()
        detector.hold_start = None
        detector.locked = False
        detector.release_count = 0

    def confirm_with_gesture(self, student, amount_paise):
        """Require the recognized student and a fresh thumbs-up; no liveness challenge."""
        detector = GestureConfirmation()
        start = time.perf_counter()
        print("\n--- Payment Confirmation ---")
        print("Look at the camera and hold a thumbs-up to confirm payment.")
        print("Press Q at any time to cancel.")

        try:
            while time.perf_counter() - start < CONFIRM_TIMEOUT:
                success, frame = self.camera.read()
                if not success:
                    print("Payment cancelled: could not read webcam frame.")
                    return False

                faces = self.find_faces(frame)
                identity_ok = (
                    len(faces) == 1
                    and faces[0][2] is not None
                    and faces[0][2].get("student_id") == student["student_id"]
                )
                confirmed = False
                display_frame = cv2.flip(frame, 1)

                if not identity_ok:
                    self.reset_gesture_state(detector)
                    status_text, status_color = "Face not verified - show one registered face", (0, 0, 255)
                else:
                    display_frame, confirmed = detector.process_frame(display_frame)
                    status_text, status_color = "Face verified - hold thumbs-up", (0, 255, 0)

                now = time.perf_counter()
                put_text(display_frame, f"{student['name']} - pay {rs(amount_paise)}",
                         (20, 75), (255, 255, 0), 0.7)
                put_text(display_frame, status_text, (20, 105), status_color, 0.6)
                put_text(display_frame,
                         f"Time left: {max(0, int(CONFIRM_TIMEOUT - (now - start)))}s",
                         (20, 135), (255, 255, 255))
                cv2.imshow("FacePay - Payment Confirmation", display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("Payment confirmation cancelled.")
                    return False

                if confirmed:
                    # Re-check the identity immediately before returning authorization.
                    if not self.final_identity_check(student["student_id"]):
                        print("Payment cancelled: final identity verification failed.")
                        return False
                    print("Face recognition and gesture confirmation passed.")
                    return True

            print("Payment confirmation timed out.")
            return False
        finally:
            detector.close()
            cv2.destroyAllWindows()

    def final_identity_check(self, student_id):
        for _ in range(3):
            success, frame = self.camera.read()
            if not success:
                return False
            faces = self.find_faces(frame)
            if (len(faces) != 1 or faces[0][2] is None
                    or faces[0][2].get("student_id") != student_id):
                return False
        return True

    def run_payment(self, student):
        student_id, student_name = student["student_id"], student["name"]

        try:
            # read the current balance directly from the database
            balance_paise = get_wallet_balance_paise(student_id)

            print("\n--- FacePay Payment ---")
            print(f"Student: {student_name}")
            print(f"Student ID: {student_id}")
            print(f"Current balance: {rs(balance_paise)}")

            amount = input("\nEnter payment amount in rupees: ").strip()

            # validate before opening the camera confirmation
            amount_paise = amount_to_paise(amount)

            if amount_paise > balance_paise:
                print("Payment rejected: insufficient wallet balance.")
                return

            print("\n--- Payment Summary ---")
            print(f"Amount: {rs(amount_paise)}")
            print(f"Balance after payment: {rs(balance_paise - amount_paise)}")

            # First use: securely enroll a PIN for this student.
            if not has_pin(student_id):
                print("\nNo payment PIN is set for this student.")
                while True:
                    pin1 = getpass("Create a 4-6 digit payment PIN: ")
                    pin2 = getpass("Confirm payment PIN: ")
                    if pin1 != pin2:
                        print("PINs do not match. Try again.")
                        continue
                    try:
                        set_pin(student_id, pin1)
                        print("Payment PIN created successfully.")
                        break
                    except ValueError as error:
                        print(error)

            # Verify PIN before opening gesture confirmation; no debit occurs on failure.
            pin_ok = False
            for _ in range(3):
                entered_pin = getpass("Enter payment PIN: ")
                pin_ok, pin_message = verify_pin(student_id, entered_pin)
                print(pin_message)
                if pin_ok:
                    break
                if "locked" in pin_message.casefold():
                    return
            if not pin_ok:
                print("Payment rejected: PIN verification failed.")
                return

            # No wallet deduction happens before PIN and gesture confirmation.
            if not self.confirm_with_gesture(student, amount_paise):
                print("Payment cancelled: gesture not confirmed.")
                return

            result = process_payment(student_id, amount)

            print("\n========== PAYMENT SUCCESSFUL ==========")
            print(f"Student: {student_name}")
            print(f"Transaction ID: {result['transaction_id']}")
            print(f"Amount: {rs(result['amount_paise'])}")
            print(f"Previous balance: {rs(result['previous_balance_paise'])}")
            print(f"New balance: {rs(result['new_balance_paise'])}")
            print("========================================")

        except InvalidAmountError as error:
            print(f"Invalid payment amount: {error}")

        except (InsufficientBalanceError, StudentNotFoundError) as error:
            print(f"Payment rejected: {error}")

        except KeyboardInterrupt:
            print("\nPayment interrupted.")

        except Exception as error:
            print(f"Payment failed: {error}")

    def run(self):
        while True:
            student = self.recognize_live()

            if student is None:
                print("No payment initiated.")
                if input("\nTry again? Type Y to continue: ").strip().casefold() != "y":
                    break
                continue

            self.run_payment(student)
            self.refresh_cache()

            if input("\nProcess another payment? Type Y to continue: ").strip().casefold() != "y":
                break

        print("\nFacePay session ended.")


def main():
    print("================================")
    print("       FACEPAY MVP")
    print("================================")

    try:
        known_encodings, known_names = load_encodings()
        student_cache = load_student_cache()
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"FacePay startup error: {error}")
        return

    print(f"Loaded {len(set(known_names))} registered face identities.")
    print(f"Loaded {len(student_cache)} student records.")

    camera = open_camera()
    if camera is None:
        print("Error: Could not open webcam.")
        return

    try:
        FacePayApp(camera, known_encodings, known_names, student_cache).run()
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()