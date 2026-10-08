import cv2
import face_recognition
import pickle
import os


# Load saved encodings
encoding_file = "data/encodings.pkl"

if not os.path.exists(encoding_file):
    print("Error: No registered students found.")
    print("Run register_student.py first.")
    exit()

with open(encoding_file, "rb") as file:
    data = pickle.load(file)

known_face_encodings = data["encodings"]
known_face_names = data["names"]

# Get unique students
registered_students = sorted(set(known_face_names))

print(f"Loaded {len(registered_students)} registered student.")

if len(registered_students) != 1:
    print(f"Loaded {len(registered_students)} registered students.")

print("Students:")

for name in registered_students:
    print(f"- {name}")


# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()


while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Detect faces
    face_locations = face_recognition.face_locations(
        rgb_frame
    )

    # Generate encodings
    face_encodings = face_recognition.face_encodings(
        rgb_frame,
        face_locations
    )

    for face_encoding, face_location in zip(
        face_encodings,
        face_locations
    ):

        # Compare with all saved encodings
        matches = face_recognition.compare_faces(
            known_face_encodings,
            face_encoding,
            tolerance=0.5
        )

        name = "Unknown"

        if True in matches:

            matched_names = []

            for i, match in enumerate(matches):

                if match:
                    matched_names.append(
                        known_face_names[i]
                    )

            if matched_names:

                name = max(
                    set(matched_names),
                    key=matched_names.count
                )

        # Face coordinates
        top, right, bottom, left = face_location

        # Draw box
        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            2
        )

        # Display name
        cv2.putText(
            frame,
            name,
            (left, bottom + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "FacePay - Face Recognition",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()