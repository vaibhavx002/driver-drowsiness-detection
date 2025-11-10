import os
import cv2
import dlib
import numpy as np
import gradio as gr
from scipy.spatial import distance as dist
from pydub import AudioSegment
from pydub.playback import play
import threading
import urllib.request
import bz2

# -----------------------------
# Setup model path and download if missing
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
# Load Dlib Face Detector + Landmark Predictor
# -----------------------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

# -----------------------------
# Eye Aspect Ratio (EAR) function
# -----------------------------
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# -----------------------------
# Beep alert for drowsiness
# -----------------------------
def play_beep():
    try:
        # Simple 1kHz tone
        tone = AudioSegment.sine(frequency=1000, duration=800)
        play(tone)
    except Exception as e:
        print("Beep error:", e)

# -----------------------------
# Drowsiness Detection Logic
# -----------------------------
EYE_AR_THRESH = 0.23
EYE_AR_CONSEC_FRAMES = 12  # Adjust for sensitivity (12 ≈ 0.6s if 20 FPS)
COUNTER = 0
ALARM_ON = False

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

        cv2.putText(frame, status, (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        break  # Only first face for better performance

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# -----------------------------
# Frame processing function
# -----------------------------
def process_video(frame):
    if frame is None:
        return None
    return detect_drowsiness(frame)

# -----------------------------
# Gradio Interface
# -----------------------------
demo = gr.Interface(
    fn=process_video,
    inputs=gr.Image(sources="webcam", streaming=True, label="🚘 Live Monitoring Feed"),
    outputs=gr.Image(label="Drowsiness Detection"),
    live=True,
    title="🚗 Driver Drowsiness Detection System",
    description="Real-time monitoring using facial landmarks & EAR method with alert beep when drowsiness detected.",
)

# -----------------------------
# Render Deployment Entry Point
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))  # Render dynamically assigns a port
    print(f"🚀 Starting app on port {port}")
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
        share=False,
        prevent_thread_lock=True  # Critical for Render to detect open port
    )
