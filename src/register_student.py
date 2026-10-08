import cv2
import face_recognition
import pickle
import os
import time


# Create main folder
os.makedirs("data/faces", exist_ok=True)

# Get student name
student_name = input("Enter student name: ").strip()

if not student_name:
    print("Error: Student name cannot be empty.")
    exit()

# Encoding file
encoding_file = "data/encodings.pkl"

# Load existing data
if os.path.exists(encoding_file):
    with open(encoding_file, "rb") as file:
        data = pickle.load(file)
else:
    data = {
        "encodings": [],
        "names": []
    }

# Check duplicate
if student_name in data["names"]:
    print(f"Error: {student_name} is already registered.")
    exit()

# Create student's folder
student_folder = f"data/faces/{student_name}"
os.makedirs(student_folder, exist_ok=True)

# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("\nFacePay Registration")
print("--------------------")
print(f"Student: {student_name}")
print("Look at the camera.")
print("Move your head slowly in different directions.")
print("The system will automatically capture 7 samples.")
print("Close the window to cancel.\n")

sample_count = 0
total_samples = 7
last_capture_time = 0
capture_interval = 1.2

while True:

    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read camera.")
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

    # One face detected
    if len(face_locations) == 1:

        top, right, bottom, left = face_locations[0]

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Samples: {sample_count}/{total_samples}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Move your head slowly",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        current_time = time.time()

        # Capture sample
        if current_time - last_capture_time >= capture_interval:

            encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations
            )

            if len(encodings) > 0:

                encoding = encodings[0]

                data["encodings"].append(encoding)
                data["names"].append(student_name)

                sample_count += 1
                last_capture_time = current_time

                image_path = (
                    f"{student_folder}/"
                    f"{student_name}_{sample_count}.jpg"
                )

                cv2.imwrite(
                    image_path,
                    frame
                )

                print(
                    f"Sample {sample_count}/{total_samples} captured"
                )

    # No face
    elif len(face_locations) == 0:

        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # Multiple faces
    else:

        cv2.putText(
            frame,
            "Multiple faces detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "FacePay - Registration",
        frame
    )

    cv2.waitKey(1)

    # Check if window is closed
    try:

        if cv2.getWindowProperty(
            "FacePay - Registration",
            cv2.WND_PROP_VISIBLE
        ) < 1:

            print("\nRegistration cancelled.")
            break

    except:

        break

    # Finish registration
    if sample_count >= total_samples:
        break


# Save encodings
if sample_count == total_samples:

    with open(
        encoding_file,
        "wb"
    ) as file:

        pickle.dump(
            data,
            file
        )

    print("\nRegistration successful!")
    print(f"Student: {student_name}")
    print(f"Samples captured: {sample_count}")
    print(f"Total encodings: {len(data['encodings'])}")
    print(f"Saved to: {encoding_file}")

else:

    print("\nRegistration incomplete.")
    print("No changes were saved.")


# Release camera
cap.release()
cv2.destroyAllWindows()