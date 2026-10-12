import math
import time
from collections import deque

import cv2
import mediapipe as mp

FINGERS = [(6, 8), (10, 12), (14, 16), (18, 20)]  # (PIP, TIP)


class GestureConfirmation:
    def __init__(self, hold_seconds=0.8, max_tilt=40, history_size=8, stable_ratio=0.7, release_frames=5):
        if hold_seconds <= 0 or history_size < 1 or release_frames < 1 or not 0 < stable_ratio <= 1:
            raise ValueError("Invalid gesture settings.")

        self.hold_seconds = hold_seconds
        self.max_tilt = max_tilt
        self.stable_ratio = stable_ratio
        self.release_frames = release_frames

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )

        self.history = deque(maxlen=history_size)
        self.hold_start = None
        self.locked = False
        self.release_count = 0

    def is_thumbs_up(self, p):
        if len(p) != 21:
            return False

        palm = math.dist(p[0], p[9])
        if palm < 1:
            return False

        # thumb must point upward, not sideways or down
        rise = p[2][1] - p[4][1]
        if rise <= 0:
            return False

        # four fingers folded: tip closer to wrist than PIP
        folded = all(math.dist(p[t], p[0]) < math.dist(p[k], p[0]) for k, t in FINGERS)

        # thumb extended away from the palm
        extended = math.dist(p[4], p[5]) > 0.6 * palm and math.dist(p[4], p[0]) > math.dist(p[3], p[0])

        # thumb angle from straight up
        tilt = math.degrees(math.atan2(abs(p[4][0] - p[2][0]), rise))

        # thumb tip clearly above every fingertip
        above = p[4][1] < min(p[t][1] for _, t in FINGERS) - 0.2 * palm

        return folded and extended and above and tilt <= self.max_tilt

    def update(self, detected):
        self.history.append(bool(detected))
        stable = (
            len(self.history) >= max(3, self.history.maxlen // 2)
            and sum(self.history) >= self.stable_ratio * len(self.history)
        )
        progress, confirmed = 0.0, False

        if stable:
            self.release_count = 0
            if self.locked:
                progress = 1.0
            else:
                self.hold_start = self.hold_start or time.perf_counter()
                progress = min(1.0, (time.perf_counter() - self.hold_start) / self.hold_seconds)
                if progress >= 1.0:
                    self.locked = confirmed = True
        else:
            self.hold_start = None
            # re-arm only after several consecutive frames without a thumbs-up
            self.release_count = 0 if detected else self.release_count + 1
            if self.release_count >= self.release_frames:
                self.locked = False

        return stable, progress, confirmed

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        detected = False

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            self.mp_drawing.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
            detected = self.is_thumbs_up([(l.x * w, l.y * h) for l in hand.landmark])

        stable, progress, confirmed = self.update(detected)

        if self.locked:
            label, color = "CONFIRMED - RELEASE GESTURE", (0, 255, 0)
        elif stable:
            label, color = "Hold thumbs up...", (0, 255, 255)
        else:
            label, color = "Show thumbs up", (0, 0, 255)

        cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        bar_w = min(300, max(1, w - 40))
        cv2.rectangle(frame, (20, h - 40), (20 + bar_w, h - 22), (255, 255, 255), 1)
        if progress > 0:
            cv2.rectangle(frame, (20, h - 40), (20 + int(bar_w * progress), h - 22), color, -1)

        return frame, confirmed

    def close(self):
        self.hands.close()


def main():
    detector = GestureConfirmation()
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        detector.close()
        print("Error: Could not open webcam.")
        return

    print("Hold a thumbs-up to confirm. Release before confirming again. Press Q to exit.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Error: Could not read webcam frame.")
                break

            frame, confirmed = detector.process_frame(cv2.flip(frame, 1))
            if confirmed:
                print("Gesture CONFIRMED")

            cv2.imshow("FacePay - Gesture Confirmation", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()