import cv2
import mediapipe as mp
import collections
import time
import threading
import speech_recognition as sr
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

cap = cv2.VideoCapture(0)

HISTORY_LEN = 5
left_y_hist = collections.deque(maxlen=HISTORY_LEN)
right_y_hist = collections.deque(maxlen=HISTORY_LEN)
left_x_hist = collections.deque(maxlen=HISTORY_LEN)
right_x_hist = collections.deque(maxlen=HISTORY_LEN)

phase_67 = 0
DETECTION_COOLDOWN_67 = 0.3
last_detection_67 = 0
gesture_counter_67 = 0
audio_counter_67 = 0
THRESH_Y = 0.02

kaby_phase = 0
kaby_last = 0
KABY_COOLDOWN = 0.4
kaby_counter = 0

GOAL = 10
PRIZE_UNLOCKED = False

def get_hand_center_y(hand_landmarks):
    indices = [0, 1, 2, 5, 9, 13, 17]
    return sum([hand_landmarks.landmark[i].y for i in indices]) / len(indices)

def palm_up(hand):
    wrist = hand.landmark[0].y
    index_mcp = hand.landmark[5].y
    pinky_mcp = hand.landmark[17].y
    return index_mcp < wrist and pinky_mcp < wrist

def listen_for_67():
    global audio_counter_67
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, phrase_time_limit=3)
            text = recognizer.recognize_google(audio)
            if "67" in text or "sixty seven" in text.lower():
                audio_counter_67 += 1
                print("Audio detected '67':", audio_counter_67)
        except Exception:
            pass

audio_thread = threading.Thread(target=listen_for_67, daemon=True)
audio_thread.start()

with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    start_time = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(frame_rgb)

        left_center_y = None
        right_center_y = None
        left_center_x = None
        right_center_x = None

        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            left_center_y = get_hand_center_y(results.left_hand_landmarks)
            left_y_hist.append(left_center_y)
            left_center_x = results.left_hand_landmarks.landmark[0].x
            left_x_hist.append(left_center_x)

        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            right_center_y = get_hand_center_y(results.right_hand_landmarks)
            right_y_hist.append(right_center_y)
            right_center_x = results.right_hand_landmarks.landmark[0].x
            right_x_hist.append(right_center_x)

        if len(left_y_hist) == HISTORY_LEN and len(right_y_hist) == HISTORY_LEN:
            dy_left = left_y_hist[-1] - left_y_hist[0]
            dy_right = right_y_hist[-1] - right_y_hist[0]
            if phase_67 == 0 and dy_left < -THRESH_Y and dy_right > THRESH_Y:
                phase_67 = 1
            elif phase_67 == 1 and dy_left > THRESH_Y and dy_right < -THRESH_Y:
                current_time = time.time()
                if current_time - last_detection_67 > DETECTION_COOLDOWN_67:
                    gesture_counter_67 += 1
                    last_detection_67 = current_time
                    phase_67 = 0
                    print("67 gestures detected:", gesture_counter_67)

        if len(left_x_hist) == HISTORY_LEN and len(right_x_hist) == HISTORY_LEN:
            dx_left = left_x_hist[-1] - left_x_hist[0]
            dx_right = right_x_hist[-1] - right_x_hist[0]
            left_up = results.left_hand_landmarks and palm_up(results.left_hand_landmarks)
            right_up = results.right_hand_landmarks and palm_up(results.right_hand_landmarks)
            if kaby_phase == 0:
                if dx_left < 0 and dx_right > 0 and left_up and right_up:
                    kaby_phase = 1
            elif kaby_phase == 1:
                current_time = time.time()
                if abs(dx_left) > 0.03 and abs(dx_right) > 0.03:
                    if current_time - kaby_last > KABY_COOLDOWN:
                        kaby_counter += 1
                        kaby_last = current_time
                        print("Khaby Lame gesture detected:", kaby_counter)
                    kaby_phase = 0

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)

        total_score = gesture_counter_67 + audio_counter_67 + kaby_counter
        progress = min(total_score / GOAL, 1.0)
        h, w, _ = frame.shape
        bar_w = int(w * 0.6)
        bar_h = 28
        bar_x = int((w - bar_w) / 2)
        bar_y = 20
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        filled_w = int(bar_w * progress)
        if progress < 0.5:
            color = (0, 0, 255)
        elif progress < 0.9:
            color = (0, 215, 255)
        else:
            color = (0, 255, 0)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), color, -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 2)
        cv2.putText(frame, f"Goal: {total_score}/{GOAL}", (bar_x + 10, bar_y + bar_h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv2.putText(frame, f"Gesture 67: {gesture_counter_67}", (10, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        cv2.putText(frame, f"Audio 67: {audio_counter_67}", (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, f"Khaby: {kaby_counter}", (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        if not PRIZE_UNLOCKED and total_score >= GOAL:
            PRIZE_UNLOCKED = True
            prize_start = time.time()

        if PRIZE_UNLOCKED:
            elapsed = time.time() - prize_start
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.putText(frame, "PRIZE UNLOCKED!", (int(w*0.12), int(h*0.4)), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255,215,0), 5)
            cv2.putText(frame, "You hit 670!", (int(w*0.34), int(h*0.5)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3)
            num_confetti = 80
            for i in range(num_confetti):
                np.random.seed(i + int(elapsed*100))
                cx = int(np.random.rand() * w)
                cy = int(np.random.rand() * h)
                r = int(3 + np.random.rand() * 8)
                cv2.circle(frame, (cx, cy), r, (int(np.random.rand()*255), int(np.random.rand()*255), int(np.random.rand()*255)), -1)
            if elapsed > 8:
                PRIZE_UNLOCKED = False
                gesture_counter_67 = 0
                audio_counter_67 = 0
                kaby_counter = 0

        cv2.imshow("67 Motion + Audio + Goal", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
