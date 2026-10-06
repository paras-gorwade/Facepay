import cv2
import time

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

prev_time = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Calculate FPS
    current_time = time.time()

    if prev_time != 0:
        fps = 1 / (current_time - prev_time)
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    prev_time = current_time

    cv2.imshow("FacePay - Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()