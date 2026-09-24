# Smart Vision

**AI-powered surveillance system with behaviour analysis, weapon detection, and face recognition.**

## 📌 Overview

Smart Vision is a prototype AI-based surveillance system designed to assist in monitoring environments using computer vision and machine learning techniques.

The system combines multiple AI capabilities to identify potentially suspicious activities and detected objects while providing a web-based interface for monitoring.

> **Note:** This project is a prototype and is still under development. Detection and recognition results may not always be accurate and should not be treated as a replacement for human supervision.

---

## 🚀 Features

* **Behaviour Analysis** — Analyzes movement patterns to identify behaviours such as loitering and running.
* **Weapon Detection** — Uses YOLO-based object detection for identifying potential weapons.
* **Face Detection** — Detects faces from camera input.
* **Face Recognition** — Attempts to recognize registered individuals.
* **Web Dashboard** — Provides a browser-based interface for surveillance monitoring.
* **Alert Handling** — Supports detection-related alert processing.
* **Firebase Integration** — Provides database connectivity for supported application features.
* **Cloud Storage Support** — Supports Cloudinary-based storage configuration.

---

## 📁 Project Structure

```text
smart-vision/
│
├── app.py
├── behavior_pose_analysis.py
├── requirements.txt
│
├── scripts/
│   ├── ai_surveillance.py
│   ├── face_detection.py
│   ├── face_recognition_live.py
│   └── weapon_detection_live.py
│
├── templates/
│   ├── dashboard.html
│   ├── login.html
│   └── surveillance.html
│
├── weapon_detection/
│   ├── code/
│   │   ├── download_model.py
│   │   ├── test_model.py
│   │   └── train.py
│   │
│   └── detect/
│       ├── smart_vision_v1/
│       └── smart_vision_v12/
│
├── firebase/
│   └── test.py
│
├── config.env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Technologies Used

* **Python**
* **Flask**
* **OpenCV**
* **YOLO**
* **Face Recognition**
* **Firebase**
* **Cloudinary**
* **HTML / CSS / JavaScript**

---

## 🔧 Setup

### 1. Clone the Repository

```bash
git clone https://github.com/saranya6789/smart-vision.git
cd smart-vision
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy:

```text
config.env.example
```

to:

```text
config.env
```

Then add your own configuration values.

> **Important:** Never upload `config.env`, API keys, passwords, or private Firebase credentials to GitHub.

### 5. Run the Application

```bash
python app.py
```

Then open the local address shown by the Flask application in your browser.

---

## 🔐 Security

Sensitive configuration files are intentionally excluded from the repository.

Do **not** upload:

```text
config.env
.env
firebase_key.json
Known_Faces/
```

API keys, passwords, database credentials, and other private credentials should always be stored locally or through a secure secrets-management system.

---

## ⚠️ Limitations

This project is currently a **prototype**.

* AI detection results may contain false positives or false negatives.
* Face recognition performance can vary depending on lighting, camera quality, and other conditions.
* Weapon detection depends on the trained detection model and available input data.
* Behaviour analysis is based on predefined detection logic and may not correctly interpret every real-world situation.
* The system requires further testing and development before use in real-world security environments.

---

## 🔮 Future Improvements

Possible future improvements include:

* Improved detection accuracy
* More robust behaviour analysis
* Better face recognition under different conditions
* Real-time notification improvements
* Improved database and cloud integration
* Additional security and authentication mechanisms
* Deployment optimization
* More extensive testing using diverse real-world scenarios

---

## 📌 Project Status

**Status: Prototype / Under Development**

Smart Vision is developed as an academic/project prototype for exploring the application of AI and computer vision techniques in surveillance systems.
