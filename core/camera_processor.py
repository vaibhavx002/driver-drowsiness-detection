# core/camera_processor.py

import threading
import time
import logging
import cv2
import mediapipe as mp
from .ear_detector import eye_aspect_ratio, LEFT_EYE_IDX, RIGHT_EYE_IDX

logging.getLogger(__name__).setLevel(logging.INFO)


class CameraProcessor(threading.Thread):
    """
    Handles camera capture → MediaPipe FaceMesh → EAR drowsiness detection.
    """

    def __init__(self, cam_index=0, ear_threshold=0.23, consecutive_frames=15):
        super().__init__(daemon=True)
        self.cam_index = cam_index
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames

        # GUI callback hooks
        self.on_drowsy = None
        self.on_clear_drowsy = None
        self.on_noface = None
        self.on_clear_noface = None

        # State
        self.stop_event = threading.Event()
        self.frame_counter = 0
        self._drowsy = False
        self.no_face_start_time = None
        self.no_face_alert_triggered = False
        self.latest_frame = None

        # MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None

        # Image adjust
        self.brightness = 0.0
        self.contrast = 1.0
        self.sharpen = 0.0
        self.auto_adjust = False

    def start_processing(self):
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            refine_landmarks=True,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.cap = cv2.VideoCapture(self.cam_index)
        if not self.cap.isOpened():
            logging.error("Failed to open camera")
            return False

        self.start()
        return True

    def run(self):
        try:
            while not self.stop_event.is_set():
                ok, frame = self.cap.read()
                if not ok:
                    time.sleep(0.02)
                    continue

                frame = cv2.flip(frame, 1)
                img_h, img_w = frame.shape[:2]

                # Auto/Manual adjust
                if self.auto_adjust:
                    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    lab = cv2.merge((l, a, b))
                    frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                else:
                    if self.sharpen > 0:
                        blur = cv2.GaussianBlur(frame, (5, 5), 0)
                        frame = cv2.addWeighted(frame, 1.0 + self.sharpen, blur, -self.sharpen, 0)
                    if self.contrast != 1.0 or self.brightness != 0:
                        frame = cv2.convertScaleAbs(frame, alpha=self.contrast, beta=self.brightness)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb)
                current_time = time.time()

                if results.multi_face_landmarks:
                    # Face visible
                    self.no_face_start_time = None
                    if self.no_face_alert_triggered:
                        self.no_face_alert_triggered = False
                        if self.on_clear_noface: self.on_clear_noface()

                    lms = results.multi_face_landmarks[0].landmark
                    left = eye_aspect_ratio(lms, LEFT_EYE_IDX, img_w, img_h)
                    right = eye_aspect_ratio(lms, RIGHT_EYE_IDX, img_w, img_h)
                    ear = (left + right) / 2.0

                    if ear < self.ear_threshold:
                        self.frame_counter += 1
                    else:
                        self.frame_counter = 0
                        if self._drowsy:
                            self._drowsy = False
                            if self.on_clear_drowsy: self.on_clear_drowsy()

                    if self.frame_counter >= self.consecutive_frames:
                        if not self._drowsy:
                            self._drowsy = True
                            if self.on_drowsy: self.on_drowsy()

                    color = (0, 0, 255) if self._drowsy else (0, 255, 0)
                    for lm in lms:
                        x = int(lm.x * img_w)
                        y = int(lm.y * img_h)
                        cv2.circle(frame, (x, y), 1, color, -1)

                else:
                    # No face
                    self.frame_counter = 0
                    if self._drowsy:
                        self._drowsy = False
                        if self.on_clear_drowsy: self.on_clear_drowsy()

                    if self.no_face_start_time is None:
                        self.no_face_start_time = current_time
                    if current_time - self.no_face_start_time > 5:
                        if not self.no_face_alert_triggered:
                            self.no_face_alert_triggered = True
                            if self.on_noface: self.on_noface()

                self.latest_frame = frame
                time.sleep(0.01)

        finally:
            if self.cap: self.cap.release()
            if self.face_mesh: self.face_mesh.close()

    def stop(self):
        self.stop_event.set()
        self.join(timeout=1.5)
