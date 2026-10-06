import cv2
import face_recognition

# -----------------------------
# Load known face
# -----------------------------

known_image = cv2.imread("data/faces/paras.jpeg")

if known_image is None:
    print("Error: Could not load paras.jpeg")
    exit()

# OpenCV: BGR → face_recognition: RGB
known_image = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)

known_image = known_image.astype("uint8")
known_image = __import__("numpy").ascontiguousarray(known_image)


encodings = face_recognition.face_encodings(known_image)

if len(encodings) == 0:
    print("Error: No face found in paras.jpeg")
    exit()

known_encoding = encodings[0]

known_face_encodings = [known_encoding]
known_face_names = ["Paras"]


# -----------------------------
# Start webcam
# -----------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()


# -----------------------------
# Face recognition loop
# -----------------------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # OpenCV BGR → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_frame)

    # Generate embeddings
    face_encodings = face_recognition.face_encodings(
        rgb_frame,
        face_locations
    )

    for face_encoding, face_location in zip(
        face_encodings,
        face_locations
    ):

        # Compare with known face
        matches = face_recognition.compare_faces(
            known_face_encodings,
            face_encoding
        )

        name = "Unknown"

        if True in matches:
            name = "Paras"

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