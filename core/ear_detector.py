# core/ear_detector.py
import math

LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]


def euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def eye_aspect_ratio(landmarks, eye_idx, img_w, img_h):
    pts = [(int(landmarks[idx].x * img_w), int(landmarks[idx].y * img_h)) for idx in eye_idx]
    p1, p2, p3, p4, p5, p6 = pts
    A = euclidean(p2, p6)
    B = euclidean(p3, p5)
    C = euclidean(p1, p4)
    return 0.0 if C == 0 else (A + B) / (2.0 * C)
