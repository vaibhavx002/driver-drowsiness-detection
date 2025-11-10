import cv2
import dlib
import numpy as np
import gradio as gr
import os
import urllib.request
from scipy.spatial import distance as dist

# -----------------------------
# Model Setup
# -----------------------------
MODEL_PATH = "Files/shape_predictor_68_face_landmarks.dat"
MODEL_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

if not os.path.exists(MODEL_PATH):
    os.makedirs("Files", exist_ok=True)
    print("🔽 Downloading dlib facial landmark model (~100MB compressed)...")
    urllib.request.urlretrieve(MODEL_URL, "Files/shape_predictor_68_face_landmarks.dat.bz2")
    import bz2
    with bz2.BZ2File("Files/shape_predictor_68_face_landmarks.dat.bz2") as fr, open(MODEL_PATH, "wb") as fw:
        fw.write(fr.read())
    print("✅ Model ready at:", MODEL_PATH)

# -----------------------------
# Drowsiness Detection Logic
# -----------------------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def detect_drowsiness(frame):
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
            status = "Drowsy 💤"
            color = (0, 0, 255)

        cv2.putText(frame, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def process_video(frame):
    if frame is None:
        return None
    return detect_drowsiness(frame)

# -----------------------------
# Gradio Interface
# -----------------------------
demo = gr.Interface(
    fn=process_video,
    inputs=gr.Image(sources="webcam", streaming=True, label="Live Webcam Feed"),
    outputs=gr.Image(label="Processed Output"),
    title="🚗 Driver Drowsiness Detection",
    description="Detects driver drowsiness in real-time using webcam and facial landmarks."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
