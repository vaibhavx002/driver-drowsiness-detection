import cv2
import dlib
import numpy as np
import gradio as gr
import os
import urllib.request
import bz2
from scipy.spatial import distance as dist

# -----------------------------
# Setup Dlib Model
# -----------------------------
MODEL_DIR = "Files"
MODEL_PATH = os.path.join(MODEL_DIR, "shape_predictor_68_face_landmarks.dat")
MODEL_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

if not os.path.exists(MODEL_PATH):
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("🔽 Downloading dlib facial landmark model (~100MB compressed)...")
    urllib.request.urlretrieve(MODEL_URL, os.path.join(MODEL_DIR, "model.bz2"))
    with bz2.BZ2File(os.path.join(MODEL_DIR, "model.bz2")) as fr, open(MODEL_PATH, "wb") as fw:
        fw.write(fr.read())
    print("✅ Model ready at:", MODEL_PATH)

# -----------------------------
# Initialize Dlib
# -----------------------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# -----------------------------
# Helper Function: Eye Aspect Ratio
# -----------------------------
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# -----------------------------
# Drowsiness Detection Logic
# -----------------------------
def detect_drowsiness(frame):
    if frame is None:
        return None

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

        if ear < 0.23:
            status = "Sleeping 💤"
            color = (0, 0, 255)
            cv2.putText(frame, "ALERT: DRIVER DROWSY!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        cv2.putText(frame, status, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# -----------------------------
# Gradio App
# -----------------------------
demo = gr.Interface(
    fn=detect_drowsiness,
    inputs=gr.Image(sources="webcam", streaming=True, label="Live Driver Feed"),
    outputs=gr.Image(label="Drowsiness Detection"),
    title="🚗 Driver Drowsiness Detection (Live)",
    description=(
        "Monitors live webcam feed to detect if the driver is drowsy or asleep. "
        "Uses eye aspect ratio and facial landmarks via Dlib."
    ),
)

# -----------------------------
# Launch App (for local + Render)
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port, share=True)
