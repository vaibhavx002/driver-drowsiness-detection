import os
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
from pydub import AudioSegment
from pydub.playback import play
import threading
import urllib.request
import bz2
import gradio as gr

# -----------------------------
# MODEL SETUP
# -----------------------------
MODEL_PATH = "Files/shape_predictor_68_face_landmarks.dat"
MODEL_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

if not os.path.exists(MODEL_PATH):
    os.makedirs("Files", exist_ok=True)
    print("🔽 Downloading dlib facial landmark model (~100MB compressed)...")
    urllib.request.urlretrieve(MODEL_URL, "Files/shape_predictor_68_face_landmarks.dat.bz2")
    with bz2.BZ2File("Files/shape_predictor_68_face_landmarks.dat.bz2") as fr, open(MODEL_PATH, "wb") as fw:
        fw.write(fr.read())
    print("✅ Model ready at:", MODEL_PATH)

# -----------------------------
# DLIB FACE + LANDMARK PREDICTOR
# -----------------------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# -----------------------------
# EYE ASPECT RATIO FUNCTION
# -----------------------------
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# -----------------------------
# SOUND ALERT (BEEP)
# -----------------------------
def play_beep():
    try:
        tone = AudioSegment.sine(frequency=1200, duration=700)
        play(tone)
    except Exception as e:
        print("⚠️ Sound error:", e)

# -----------------------------
# DROWSINESS DETECTION VARIABLES
# -----------------------------
EYE_AR_THRESH = 0.23
EYE_AR_CONSEC_FRAMES = 12
COUNTER = 0
ALARM_ON = False

# -----------------------------
# DROWSINESS DETECTION FUNCTION
# -----------------------------
def detect_drowsiness(frame):
    global COUNTER, ALARM_ON

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    status = "Awake 😃"
    color = (0, 255, 0)

    for face in faces:
        landmarks = predictor(gray, face)
        landmarks_points = np.array([[p.x, p.y] for p in landmarks.parts()])

        left_eye = landmarks_points[36:42]
        right_eye = landmarks_points[42:48]

        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0

        if ear < EYE_AR_THRESH:
            COUNTER += 1
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                status = "Drowsy 💤"
                color = (0, 0, 255)
                if not ALARM_ON:
                    ALARM_ON = True
                    threading.Thread(target=play_beep, daemon=True).start()
        else:
            COUNTER = 0
            ALARM_ON = False

        # Overlay status on the webcam frame
        cv2.putText(frame, status, (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        break  # process only the first face for efficiency

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# -----------------------------
# GRADIO LIVE INTERFACE
# -----------------------------
def process_video(frame):
    if frame is None:
        return None
    return detect_drowsiness(frame)

demo = gr.Interface(
    fn=process_video,
    inputs=gr.Image(sources="webcam", streaming=True, label="🚘 Live Driver Monitoring"),
    outputs=gr.Image(label="Drowsiness Detection"),
    live=True,
    title="🚗 Real-Time Driver Drowsiness Detection",
    description="AI-powered system that detects if a driver is falling asleep using facial landmarks and eye aspect ratio.",
)

# -----------------------------
# FASTAPI APP FOR RENDER DEPLOYMENT
# -----------------------------
app = demo.to_fastapi()
