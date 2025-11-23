
---

# 🔥 DrowsyGuard – Real-Time Driver Drowsiness Detection

### *AI-powered | Modern Glass UI | Real-Time Facial Landmark Tracking*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Qt6-PySide6-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/OpenCV-RealTime-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/MediaPipe-FaceMesh-orange?style=for-the-badge">
</p>

---

## 🚗 Overview

**DrowsyGuard** is a real-time driver safety system that detects drowsiness using facial landmarks and EAR (Eye Aspect Ratio).
Designed with a **premium glass-morphic UI**, animated alerts, neon shockwave effects, and instant audio warnings.

Perfect for:

* Resume / Portfolio
* AI + CV showcase
* Qt UI projects
* Real-world accident-prevention system

---

## ✨ Features

### 🔍 Real-Time Detection

* MediaPipe Face Mesh (468 landmarks)
* Eye Aspect Ratio (EAR) drowsiness detection
* No-face detection alerts

### 🔥 Premium UI (PySide6 + Custom QPainter Effects)

* Glass cards with glow & fire-pulse animations
* Neon shockwave alert
* Flashing red warning panel
* Smooth transitions & hover effects

### 🔊 Alerts

* Loud beeping sound
* Flash overlay
* Shockwave ripple animation
* Red “DROWSINESS ALERT” message

### 🧱 Modular Code Structure

* `camera_processor.py`
* `ear_detector.py`
* `glass_card.py`
* `flash_overlay.py`
* `main_window.py`

---

## 📂 Project Structure

```
DrowsyGuard/
│── main.py
│── requirements.txt
│
├── core/
│   ├── camera_processor.py
│   ├── ear_detector.py
│
├── gui/
│   ├── main_window.py
│   ├── glass_card.py
│   ├── flash_overlay.py
│   ├── shockwave.py
│   ├── style.qss
│
└── assets/
    ├── alert.wav
    ├── noface.wav
```

---

## 🚀 Installation

### 1️⃣ Clone repo

```bash
git clone https://github.com/yourusername/DrowsyGuard
cd DrowsyGuard
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the app

```bash
python main.py
```

---

## ⚙️ How Drowsiness Detection Works

### 🎯 EAR Algorithm

* Detect eye coordinates from facial landmarks
* Compute EAR
* If EAR < threshold for N frames → **drowsy**

### 🤖 MediaPipe FaceMesh

* 468 face landmarks in real time
* High accuracy even in low light

### 🔔 Alert Flow

1. EAR threshold crossed
2. Flashing red overlay
3. Neon shockwave pulses
4. Warning sound plays
5. Status label changes

---

## 🛠 Tech Stack

| Component | Technology                           |
| --------- | ------------------------------------ |
| UI        | PySide6 (Qt6), QSS styling, QPainter |
| CV        | OpenCV, MediaPipe FaceMesh           |
| Logic     | EAR algorithm                        |
| Audio     | QSoundEffect                         |
| Design    | Glassmorphism + animated effects     |

---

## 📸 Screenshots

(Add yours here after uploading)

```
![Screenshot](assets/screenshot1.png)
![Alert](assets/screenshot_alert.png)
```

---

## ⭐ Why This Project Stands Out

* Real-world computer vision system
* Custom-built animated UI (not standard Qt)
* Uses AI + UI + threading
* Recruiter-friendly
* Perfect for resumes & GitHub showcase

---

## 🛡 License

MIT License © 2025

---

## 💬 Connect

If you like this project, please ⭐ star the repo!

```
LinkedIn: [https://www.linkedin.com/in/vaibhavx002/]
```

---
