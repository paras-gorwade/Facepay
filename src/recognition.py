import cv2
import face_recognition
import pickle
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENCODING_FILE = PROJECT_ROOT / "data" / "encodings.pkl"
DATABASE_PATH = PROJECT_ROOT / "database" / "facepay.db"


def load_encodings():
    """Load saved face encodings."""
    if not ENCODING_FILE.exists():
        raise FileNotFoundError(
            "No registered students found. "
            "Run register_student.py first."
        )

    with ENCODING_FILE.open("rb") as file:
        data = pickle.load(file)

    return data["encodings"], data["names"]


def load_student_cache():
    """Load student records into memory for fast lookups."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"FacePay database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT student_id, name, balance
            FROM students
            """
        ).fetchall()

    student_cache = {}

    for student_id, name, balance in rows:
        key = name.strip().casefold()

        if key in student_cache:
            raise ValueError(
                f"Duplicate student name in database: {name}. "
                "Student names must be unique for name-based lookup."
            )

        student_cache[key] = {
            "student_id": student_id,
            "name": name,
            "balance": balance,
        }

    return student_cache


def recognize_student(face_encoding, known_encodings, known_names):
    """Recognize a face using saved face encodings."""
    matches = face_recognition.compare_faces(
        known_encodings,
        face_encoding,
        tolerance=0.5,
    )

    matched_names = [
        known_names[index]
        for index, matched in enumerate(matches)
        if matched
    ]

    if not matched_names:
        return None

    return max(
        set(matched_names),
        key=matched_names.count,
    )


def main():
    # Load face encodings and database records once at startup.
    try:
        known_encodings, known_names = load_encodings()
        student_cache = load_student_cache()
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"FacePay startup error: {error}")
        return

    registered_students = sorted(set(known_names))

    print(f"Loaded {len(registered_students)} registered face identities.")
    print(f"Loaded {len(student_cache)} student database records.")
    print("Registered face identities:")

    for name in registered_students:
        print(f"- {name}")

    # Start webcam.
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Error: Could not read camera frame.")
                break

            # OpenCV uses BGR; face_recognition expects RGB.
            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            face_locations = face_recognition.face_locations(
                rgb_frame
            )

            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations,
            )

            for face_encoding, face_location in zip(
                face_encodings,
                face_locations,
            ):
                # Identify the face.
                name = recognize_student(
                    face_encoding,
                    known_encodings,
                    known_names,
                )

                # Retrieve the record from memory, not SQLite.
                student = (
                    student_cache.get(name.strip().casefold())
                    if name is not None
                    else None
                )

                if student is not None:
                    label = (
                        f"{student['name']} | "
                        f"{student['student_id']}"
                    )

                    balance_label = (
                        f"Wallet: Rs. {student['balance']:.2f}"
                    )

                    color = (0, 255, 0)

                elif name is not None:
                    label = f"{name} | Not in database"
                    balance_label = "Wallet: unavailable"
                    color = (0, 165, 255)

                else:
                    label = "Unknown"
                    balance_label = "Wallet: unavailable"
                    color = (0, 0, 255)

                # Face coordinates.
                top, right, bottom, left = face_location

                # Draw the face bounding box.
                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    color,
                    2,
                )

                # Display identity.
                cv2.putText(
                    frame,
                    label,
                    (left, max(top - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    color,
                    2,
                )

                # Display wallet balance or unavailable status.
                cv2.putText(
                    frame,
                    balance_label,
                    (left, bottom + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    color,
                    2,
                )

            cv2.imshow(
                "FacePay - Recognition and Wallet",
                frame,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()