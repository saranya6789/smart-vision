"""SmartVision Flask app for real-time face, weapon, and behavior detection."""

import atexit
import json
import math
import os
import time
import urllib.request
from datetime import datetime

from flask import Flask, render_template, Response, request, redirect, url_for, session
import cv2
import numpy as np
from deepface import DeepFace
from ultralytics import YOLO
import cloudinary
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, db

# ------------------------- Flask Setup -------------------------
app = Flask(__name__)
app.secret_key = "smartvision_secret_key"

# ------------------------- Config Paths ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "Known_Faces")
FIREBASE_KEY_PATH = os.path.join(BASE_DIR, "firebase", "firebase_key.json")
YOLO_POSE_MODEL = os.path.join(BASE_DIR, "yolov8n-pose.pt")
YOLO_WEAPON_MODEL = os.path.join(
    BASE_DIR,
    "weapon_detection",
    "detect",
    "smart_vision_v12",
    "weights",
    "best.pt",
)

# Local storage fallback directories
LOCAL_ALERTS_DIR = os.path.join(BASE_DIR, "alerts_local")
LOCAL_WEAPONS_DIR = os.path.join(BASE_DIR, "weapons_local")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

for dir_path in [LOCAL_ALERTS_DIR, LOCAL_WEAPONS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ------------------------- Firebase ----------------------------
FIREBASE_DB_URL = "https://smartvision-b3697-default-rtdb.firebaseio.com/"
DISABLE_CLOUDINARY_UPLOAD = os.getenv("DISABLE_CLOUDINARY_UPLOAD", "0").lower() in ("1", "true", "yes")
TIME_SKEW_CHECK_URL = "http://worldtimeapi.org/api/timezone/Etc/UTC"
TIME_SKEW_THRESHOLD = 300

firebase_initialized = False
db_ref = None
db_weapon_ref = None

try:
    firebase_apps = firebase_admin._apps if hasattr(firebase_admin, '_apps') else {}
    if not firebase_apps:
        print("Initializing Firebase...")
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        print("✓ Firebase app initialized.")
    else:
        print(f"Firebase app already initialized ({len(firebase_apps)} app(s) found).")
    
    db_ref = db.reference("alerts")
    db_weapon_ref = db.reference("weapon_alerts")
    
    if db_ref is not None and db_weapon_ref is not None:
        firebase_initialized = True
        print("✓ Firebase database references created successfully.")
    else:
        print("✗ Firebase database references are None.")
except Exception as e:
    print(f"✗ Firebase initialization failed: {e}")
    import traceback
    traceback.print_exc()

# ------------------------- Cloudinary --------------------------
cloudinary.config(
    cloud_name="dr5qkyjkb",
    api_key="536222354493362",
    api_secret="IXH-7itSGsWRxg4W-6xplkLpky8"
)

# ------------------------- Settings ---------------------------
MODEL_NAME = "Facenet512"
DETECTOR_BACKEND = "opencv"
THRESHOLD = 0.45
FRAME_SKIP = 5

LOITERING_TIME = 25
RUN_CENTER_SPEED = 8
MAX_HISTORY = 30

# Alert management
ALERT_COOLDOWN = 10  # seconds between same-type alerts
MAX_LOCAL_ALERTS = 500  # max images to keep locally
CLEANUP_INTERVAL = 3600  # cleanup every hour

# App metrics
app_metrics = {
    "alerts_total": 0,
    "alerts_firebase": 0,
    "alerts_local": 0,
    "cloudinary_uploads": 0,
    "cloudinary_failures": 0,
    "firebase_errors": 0,
    "start_time": datetime.now().isoformat()
}

# ------------------------- Globals ----------------------------
known_data = []
frame_count = 0
last_results = []
person_data = {}
last_alert_time = {}

# ------------------------- Load Known Faces -------------------
def cosine_distance(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0: return 1.0
    return 1 - (dot / (norm_a * norm_b))

def find_match(face_embedding):
    best_name = "Unknown"
    best_distance = 999.0
    for item in known_data:
        dist = cosine_distance(face_embedding, item["embedding"])
        if dist < best_distance:
            best_distance = dist
            best_name = item["name"]
    if best_distance < THRESHOLD: return best_name, best_distance
    return "Unknown", best_distance

def load_known_faces():
    global known_data
    if not os.path.exists(KNOWN_FACES_DIR):
        print("Known_Faces folder not found:", KNOWN_FACES_DIR)
        return False
    print("Loading known faces...")
    for person_name in os.listdir(KNOWN_FACES_DIR):
        person_folder = os.path.join(KNOWN_FACES_DIR, person_name)
        if not os.path.isdir(person_folder): continue
        for img_name in os.listdir(person_folder):
            img_path = os.path.join(person_folder, img_name)
            try:
                reps = DeepFace.represent(
                    img_path=img_path, model_name=MODEL_NAME,
                    detector_backend=DETECTOR_BACKEND, enforce_detection=True
                )
                if len(reps) > 0:
                    embedding = np.array(reps[0]["embedding"], dtype=np.float32)
                    known_data.append({"name": person_name, "embedding": embedding})
            except Exception as e:
                print(f"Skipped {img_path}: {e}")
    print(f"Total known faces: {len(known_data)}")
    return len(known_data) > 0

load_known_faces()


def cleanup_old_files():
    """Remove old local alert files to manage disk space."""
    try:
        for dir_path in [LOCAL_ALERTS_DIR, LOCAL_WEAPONS_DIR]:
            if not os.path.exists(dir_path):
                continue
            files = sorted([f for f in os.listdir(dir_path) if f.endswith('.jpg')],
                          key=lambda x: os.path.getmtime(os.path.join(dir_path, x)))
            if len(files) > MAX_LOCAL_ALERTS:
                for f in files[:-MAX_LOCAL_ALERTS]:
                    try:
                        os.remove(os.path.join(dir_path, f))
                    except Exception:
                        pass
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


def save_alert_locally(image, name, timestamp, alert_type="alert"):
    """Save alert image locally as fallback."""
    try:
        if alert_type == "weapon":
            save_dir = LOCAL_WEAPONS_DIR
        else:
            save_dir = LOCAL_ALERTS_DIR
        
        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, image)
        return filepath
    except Exception as e:
        print(f"⚠️ Local save failed: {e}")
        return None


def log_event(event_type, details):
    """Log important events for debugging."""
    try:
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {event_type}: {details}\n"
        log_file = os.path.join(LOGS_DIR, f"smartvision_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception:
        pass


def get_system_health():
    """Get system health status."""
    health = {
        "timestamp": datetime.now().isoformat(),
        "firebase_initialized": firebase_initialized,
        "firebase_available": firebase_initialized and db_ref is not None,
        "camera_available": cap is not None and cap.isOpened() if cap else False,
        "models_loaded": True,
        "metrics": app_metrics.copy()
    }
    return health

def get_network_utc_time():
    try:
        with urllib.request.urlopen(TIME_SKEW_CHECK_URL, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            utc_datetime = data.get("utc_datetime")
            if utc_datetime:
                return datetime.fromisoformat(utc_datetime.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception as e:
        print(f"⚠️ Could not fetch network UTC time: {e}")
    return None


def warn_if_clock_skewed():
    network_utc = get_network_utc_time()
    if network_utc is None:
        return
    local_utc = datetime.utcnow()
    skew = abs((network_utc - local_utc).total_seconds())
    if skew > TIME_SKEW_THRESHOLD:
        print(f"⚠️ System clock skew detected: local UTC={local_utc.isoformat()} remote UTC={network_utc.isoformat()} skew={skew:.0f}s")
        print("   Please sync the system clock and restart the application.")

warn_if_clock_skewed()


def refresh_firebase_app():
    global firebase_initialized, db_ref, db_weapon_ref
    try:
        apps = getattr(firebase_admin, "_apps", {}) if hasattr(firebase_admin, "_apps") else {}
        if apps:
            app_items = apps.values() if isinstance(apps, dict) else list(apps)
            for app_item in list(app_items):
                try:
                    firebase_admin.delete_app(app_item)
                except Exception:
                    pass
    except Exception as e:
        print(f"⚠️ Failed to cleanup Firebase apps: {e}")

    try:
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        db_ref = db.reference("alerts")
        db_weapon_ref = db.reference("weapon_alerts")
        firebase_initialized = True
        print("✓ Firebase reinitialized successfully.")
        return True
    except Exception as e:
        firebase_initialized = False
        db_ref = None
        db_weapon_ref = None
        print(f"✗ Firebase reinitialization failed: {e}")
        return False

# ------------------------- Initialize Models -------------------
print("Loading YOLO pose model...")
pose_model = YOLO(YOLO_POSE_MODEL)
print("Pose model loaded.")

print("Loading YOLO weapon model...")
weapon_model = YOLO(YOLO_WEAPON_MODEL)
print("Weapon model loaded.")

# ------------------------- Utils ------------------------------
def upload_alert(image, name, behavior=None, db_ref=db_ref):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.jpg"
        path_local = os.path.join(BASE_DIR, filename)
        
        app_metrics["alerts_total"] += 1
        
        # Save image locally
        cv2.imwrite(path_local, image)
        local_path = save_alert_locally(image, name, timestamp, "alert")
        
        image_url = ""
        cloudinary_failed = False
        
        if DISABLE_CLOUDINARY_UPLOAD:
            print("⚠️ Cloudinary upload disabled by configuration.")
        else:
            try:
                result = cloudinary.uploader.upload(path_local, folder="smartvision_alerts")
                image_url = result.get("secure_url", "")
                if image_url:
                    print(f"✓ Image uploaded to Cloudinary: {image_url}")
                    app_metrics["cloudinary_uploads"] += 1
                else:
                    print("⚠️ Cloudinary upload did not return secure_url.")
                    cloudinary_failed = True
                    app_metrics["cloudinary_failures"] += 1
            except Exception as e:
                print(f"✗ Cloudinary upload failed: {e}")
                cloudinary_failed = True
                app_metrics["cloudinary_failures"] += 1
        
        if os.path.exists(path_local):
            os.remove(path_local)

        try:
            if not firebase_initialized or db_ref is None:
                print("✗ Firebase not initialized. Storing alert locally only.")
                if local_path:
                    app_metrics["alerts_local"] += 1
                    log_event("ALERT_LOCAL_ONLY", f"{name} / {behavior}")
                return
            
            db_ref.push({
                "name": name,
                "behavior": behavior,
                "timestamp": timestamp,
                "image": image_url,
                "local_path": local_path or ""
            })
            print(f"✓ Alert sent to Firebase: {name} / {behavior}")
            app_metrics["alerts_firebase"] += 1
            log_event("ALERT_FIREBASE", f"{name} / {behavior}")
            
            if not image_url:
                print("  Alert saved without image due to Cloudinary issue.")
        except Exception as e:
            print(f"✗ Firebase push failed: {e}")
            app_metrics["firebase_errors"] += 1
            log_event("ALERT_FIREBASE_ERROR", str(e))
            
            if "invalid_grant" in str(e).lower() or "invalid jwt" in str(e).lower():
                print("  Attempting Firebase reinitialization due to invalid JWT error.")
                if refresh_firebase_app():
                    try:
                        if db_ref:
                            db_ref.push({
                                "name": name,
                                "behavior": behavior,
                                "timestamp": timestamp,
                                "image": image_url,
                                "local_path": local_path or ""
                            })
                            print("✓ Firebase alert retried successfully after reinitialization.")
                            app_metrics["alerts_firebase"] += 1
                    except Exception as e2:
                        print(f"✗ Firebase retry failed: {e2}")
                        app_metrics["firebase_errors"] += 1
            
            print(f"  Alert data: name={name}, behavior={behavior}, timestamp={timestamp}, local_path={local_path}")
            
    except Exception as e:
        print(f"✗ Alert upload failed with error: {e}")
        log_event("ALERT_ERROR", str(e))
        import traceback
        traceback.print_exc()

def point_distance(p1, p2):
    if p1 is None or p2 is None: return 0
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def get_pose_center(kpts):
    def midpoint(p1, p2):
        if p1 is None or p2 is None: return None
        return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
    def get_valid_point(kpts, idx, conf=0.3):
        if idx>=len(kpts): return None
        x,y,c=kpts[idx]
        if c>=conf: return (int(x),int(y))
        return None
    left_hip = get_valid_point(kpts,11)
    right_hip = get_valid_point(kpts,12)
    left_shoulder = get_valid_point(kpts,5)
    right_shoulder = get_valid_point(kpts,6)
    return midpoint(left_hip,right_hip) or midpoint(left_shoulder,right_shoulder)

def get_leg_speed(history_list):
    if len(history_list) < 2: return 0
    return point_distance(history_list[-1], history_list[-2])

def safe_append(history_list, value, max_len):
    history_list.append(value)
    if len(history_list) > max_len: del history_list[0]

# ------------------------- Video Capture -----------------------
cap = None
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i} opened successfully.")
        break
    cap.release()
if not cap or not cap.isOpened():
    print("Error: Could not open any camera. Video feed will not work.")
    cap = None
else:
    print("Camera opened successfully.")
    atexit.register(lambda: cap.release() if cap and cap.isOpened() else None)

# ------------------------- Flask Routes ------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        mode = request.form.get("mode")
        if username=="admin" and password=="admin":
            session["logged_in"] = True
            session["mode"] = mode
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"): return redirect(url_for("login"))
    mode = session.get("mode", "normal")
    return render_template("dashboard.html", mode=mode)

@app.route("/surveillance")
def surveillance():
    if not session.get("logged_in"): return redirect(url_for("login"))
    mode = session.get("mode", "normal")
    return render_template("surveillance.html", mode=mode)

def generate_frames(mode):
    global frame_count, last_results, person_data
    if cap is None:
        print("No camera available, cannot generate frames.")
        return
    print(f"Starting video feed in {mode} mode")
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera, yielding blank frame")
                # Yield a blank frame
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    blank,
                    "Camera not available",
                    (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )
                ret_encode, buffer = cv2.imencode(".jpg", blank)
                if ret_encode:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.1)
                continue
            display_frame = frame.copy()
            frame_count += 1

            # Face Recognition (Smart Mode Only)
            if mode == "smart" and frame_count % FRAME_SKIP == 0:
                try:
                    detections = DeepFace.extract_faces(frame, detector_backend="opencv", enforce_detection=False)
                    for det in detections:
                        area = det.get("facial_area", {})
                        x, y, w, h = area.get("x",0), area.get("y",0), area.get("w",0), area.get("h",0)
                        if w<=0 or h<=0: continue
                        face_crop = frame[y:y+h, x:x+w]
                        reps = DeepFace.represent(face_crop, model_name=MODEL_NAME, detector_backend="skip", enforce_detection=False)
                        if len(reps)==0: continue
                        embedding = np.array(reps[0]["embedding"], dtype=np.float32)
                        name,_ = find_match(embedding)
                        cv2.rectangle(display_frame,(x,y),(x+w,y+h),(0,255,0) if name!="Unknown" else (0,0,255),2)
                        cv2.putText(display_frame,name,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)
                        if name=="Unknown" and time.time()-last_alert_time.get("Unknown",0)>10:
                            upload_alert(face_crop,"Unknown","Unknown Face")
                            last_alert_time["Unknown"]=time.time()
                except Exception as e:
                    print(f"Face recognition error: {e}")

            # Weapon Detection (Both Modes)
            try:
                results_weapon = weapon_model(frame, verbose=False)
                for result in results_weapon:
                    if result.boxes is not None:
                        for box in result.boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            label = weapon_model.names[cls_id]
                            if conf < 0.5: continue
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(display_frame, f"{label} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            weapon_key = f"weapon_{label}"
                            if time.time() - last_alert_time.get(weapon_key, 0) > 10:
                                weapon_crop = frame[y1:y2, x1:x2]
                                if weapon_crop.size > 0:
                                    try:
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        filename = f"{label}_{timestamp}.jpg"
                                        path_local = os.path.join(BASE_DIR, filename)
                                        
                                        # Save image locally
                                        cv2.imwrite(path_local, weapon_crop)
                                        
                                        image_url = ""
                                        if DISABLE_CLOUDINARY_UPLOAD:
                                            print("⚠️ Cloudinary upload disabled by configuration.")
                                        else:
                                            try:
                                                result = cloudinary.uploader.upload(path_local, folder="smartvision_alerts")
                                                image_url = result.get("secure_url", "")
                                                if image_url:
                                                    print(f"✓ Weapon image uploaded to Cloudinary: {image_url}")
                                                else:
                                                    print("⚠️ Weapon image uploaded but secure_url missing.")
                                            except Exception as e:
                                                print(f"✗ Cloudinary upload failed: {e}")
                                        if os.path.exists(path_local):
                                            os.remove(path_local)

                                        try:
                                            if not firebase_initialized or db_weapon_ref is None:
                                                print("✗ Firebase not initialized. Weapon alert cannot be pushed.")
                                            else:
                                                db_weapon_ref.push({
                                                    "weapon": label,
                                                    "timestamp": timestamp,
                                                    "image": image_url
                                                })
                                                print(f"✓ Weapon alert sent to Firebase: {label}")
                                                if not image_url:
                                                    print("  Weapon alert sent without image due to Cloudinary upload issue.")
                                        except Exception as e:
                                            print(f"✗ Firebase push failed: {e}")
                                            if "invalid_grant" in str(e).lower() or "invalid jwt" in str(e).lower():
                                                print("  Attempting Firebase reinitialization due to invalid JWT error.")
                                                if refresh_firebase_app():
                                                    try:
                                                        if db_weapon_ref:
                                                            db_weapon_ref.push({
                                                                "weapon": label,
                                                                "timestamp": timestamp,
                                                                "image": image_url
                                                            })
                                                            print("✓ Weapon alert retried successfully after reinitialization.")
                                                    except Exception as e2:
                                                        print(f"✗ Firebase retry failed: {e2}")
                                    except Exception as e:
                                        print(f"✗ Weapon alert upload failed: {e}")
                                    last_alert_time[weapon_key] = time.time()
            except Exception as e:
                print(f"Weapon detection error: {e}")

            # Pose & Behavior Analysis (Smart Mode Only)
            if mode == "smart":
                try:
                    results_pose = pose_model.track(frame, persist=True, verbose=False)
                    if results_pose:
                        for res in results_pose:
                            if res.keypoints is None or res.boxes is None: continue
                            boxes = res.boxes.xyxy.cpu().numpy()
                            kpts_data = res.keypoints.data.cpu().numpy()
                            ids = res.boxes.id.cpu().numpy().astype(int) if res.boxes.id is not None else [-1]*len(boxes)
                            for track_id, box, kpts in zip(ids, boxes, kpts_data):
                                center = get_pose_center(kpts)
                                if center is None: continue
                                if track_id not in person_data:
                                    person_data[track_id] = {
                                        "first_seen": time.time(),
                                        "centers": [center],
                                        "status": "Normal"
                                    }
                                else:
                                    pdata = person_data[track_id]
                                    safe_append(pdata["centers"], center, MAX_HISTORY)
                                
                                pdata = person_data[track_id]
                                time_spent = time.time() - pdata["first_seen"]
                                center_speed = get_leg_speed(pdata["centers"])
                                
                                behavior = "Normal"
                                if time_spent >= LOITERING_TIME:
                                    behavior = "Loitering"
                                if center_speed > RUN_CENTER_SPEED:
                                    behavior = "Running"
                                
                                pdata["status"] = behavior
                                
                                color = (0,255,0) if behavior=="Normal" else (0,165,255) if behavior=="Running" else (0,0,255)
                                cv2.rectangle(display_frame,(int(box[0]),int(box[1])),(int(box[2]),int(box[3])),color,2)
                                cv2.putText(display_frame,f"ID:{track_id} {behavior}",(int(box[0]),int(box[1]-10)),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
                                
                                if behavior != "Normal":
                                    behavior_key = f"{track_id}_{behavior}"
                                    if time.time() - last_alert_time.get(behavior_key, 0) > 10:
                                        person_crop = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                                        if person_crop.size > 0:
                                            upload_alert(person_crop, f"Person_{track_id}", behavior)
                                            last_alert_time[behavior_key] = time.time()
                except Exception as e:
                    print(f"Pose analysis error: {e}")

            # Encode frame
            ret_encode, buffer = cv2.imencode(".jpg", display_frame)
            if not ret_encode:
                print("Failed to encode frame")
                # Yield a blank frame
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                ret_encode, buffer = cv2.imencode(".jpg", blank)
                if not ret_encode:
                    continue
            frame_bytes = buffer.tobytes()
            print("Yielding frame")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(0.1)
            continue

@app.route("/video_feed")
def video_feed():
    if not session.get("logged_in"): return redirect(url_for("login"))
    mode = session.get("mode", "normal")
    return Response(generate_frames(mode), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/api/health")
def health():
    """Health check endpoint - no auth required."""
    return get_system_health(), 200

@app.route("/api/metrics")
def metrics():
    """Get app metrics - no auth required."""
    from flask import jsonify
    return jsonify(app_metrics), 200

@app.route("/api/status")
def status():
    """Get detailed system status."""
    if not session.get("logged_in"): return {"error": "unauthorized"}, 401
    from flask import jsonify
    status_data = {
        "system_health": get_system_health(),
        "active_mode": session.get("mode", "normal"),
        "cloudinary_enabled": not DISABLE_CLOUDINARY_UPLOAD,
        "time_sync_status": "unknown"
    }
    return jsonify(status_data), 200

# Periodic cleanup
import threading
def background_cleanup():
    """Run cleanup tasks periodically."""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL)
            cleanup_old_files()
            log_event("CLEANUP", f"alerts_firebase={app_metrics['alerts_firebase']} alerts_local={app_metrics['alerts_local']}")
        except Exception as e:
            print(f"Background cleanup error: {e}")

cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()

# Graceful shutdown
def shutdown_handler():
    """Handle graceful shutdown."""
    print("\n\n" + "="*60)
    print("SmartVision shutting down...")
    log_event("SHUTDOWN", f"Final metrics: {app_metrics}")
    if cap:
        cap.release()
    print("✓ All resources released.")

atexit.register(shutdown_handler)

# ------------------------- Run App ---------------------------
if __name__=="__main__":
    print("\n" + "="*60)
    print("✓ SmartVision Started")
    print(f"✓ Local alerts dir: {LOCAL_ALERTS_DIR}")
    print(f"✓ Logs dir: {LOGS_DIR}")
    print(f"✓ Health check: http://localhost:5000/api/health")
    print(f"✓ Metrics: http://localhost:5000/api/metrics")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)