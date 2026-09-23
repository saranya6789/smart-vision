import cv2
import os
import time
from datetime import datetime
from ultralytics import YOLO
import cloudinary
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, db
import torch  # Needed for safe globals

# ------------------------
# CONFIGURATION
# ------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = r"C:\Users\saran\OneDrive\Desktop\SmartVision\weapon_detection\detect\smart_vision_v12\weights\best.pt"
FIREBASE_KEY_PATH = os.path.join(BASE_DIR, "firebase", "firebase_key.json")
FIREBASE_DB_URL = "https://smartvision-b3697-default-rtdb.firebaseio.com/"

cloudinary.config(
    cloud_name="dr5qkyjkb",
    api_key="536222354493362",
    api_secret="IXH-7itSGsWRxg4W-6xplkLpky8"
)

# ------------------------
# INITIALIZE FIREBASE
# ------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

db_ref = db.reference("weapon_alerts")

# ------------------------
# SAFE LOAD YOLO MODEL
# ------------------------
# Allowlist necessary classes to avoid unpickling error
with torch.serialization.safe_globals([torch.nn.modules.container.Sequential]):
    model = YOLO(MODEL_PATH)  # do NOT pass weights_only here

# ------------------------
# OPEN CAMERA
# ------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open webcam.")
    exit()

# ------------------------
# ALERT CONTROL
# ------------------------
last_alert_time = 0
ALERT_INTERVAL = 10  # seconds between alerts to avoid frequent uploads

# ------------------------
# MAIN LOOP
# ------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO detection
    results = model(frame, verbose=False)

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            label = model.names[cls_id]

            if conf < 0.5:
                continue

            # Draw box and label
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Upload alert if enough time has passed
            current_time = time.time()
            if current_time - last_alert_time > ALERT_INTERVAL:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{label}_{timestamp}.jpg"
                    local_path = os.path.join(BASE_DIR, filename)

                    cv2.imwrite(local_path, frame)

                    # Upload to Cloudinary
                    try:
                        upload_result = cloudinary.uploader.upload(local_path, folder="smartvision_weapons")
                        image_url = upload_result["secure_url"]
                        print(f"✓ Image uploaded to Cloudinary: {image_url}")
                    except Exception as e:
                        print(f"✗ Cloudinary upload failed: {e}")
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        continue

                    # Push alert to Firebase
                    try:
                        db_ref.push({
                            "weapon": label,
                            "confidence": round(conf, 2),
                            "timestamp": timestamp,
                            "image": image_url
                        })
                        print(f"✓ Weapon alert sent to Firebase: {label} / {conf:.2f}")
                    except Exception as e:
                        print(f"✗ Firebase push failed: {e}")
                        print(f"  Alert data: weapon={label}, confidence={conf:.2f}, timestamp={timestamp}")

                    # Remove local file
                    if os.path.exists(local_path):
                        os.remove(local_path)

                    last_alert_time = current_time
                except Exception as e:
                    print(f"✗ Weapon alert upload failed: {e}")
                    import traceback
                    traceback.print_exc()

    # Display the live feed
    cv2.imshow("Weapon Detection Live", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()