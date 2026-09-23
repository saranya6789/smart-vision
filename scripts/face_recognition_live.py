import os
import cv2
import numpy as np
from deepface import DeepFace

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Known_Faces"))

# ---------------------------------------------------
# SETTINGS
# ---------------------------------------------------
MODEL_NAME = "Facenet512"
DETECTOR_BACKEND = "opencv"
DISTANCE_METRIC = "cosine"
THRESHOLD = 0.45
FRAME_SKIP = 5

# ---------------------------------------------------
# STORAGE
# ---------------------------------------------------
known_data = []
last_results = []
frame_count = 0

# ---------------------------------------------------
# LOAD KNOWN FACES ONCE
# ---------------------------------------------------
def load_known_faces():
    global known_data

    if not os.path.exists(KNOWN_FACES_DIR):
        print("Known_Faces folder not found:", KNOWN_FACES_DIR)
        return False

    print("Loading known faces...")

    for person_name in os.listdir(KNOWN_FACES_DIR):
        person_folder = os.path.join(KNOWN_FACES_DIR, person_name)

        if not os.path.isdir(person_folder):
            continue

        for img_name in os.listdir(person_folder):
            img_path = os.path.join(person_folder, img_name)

            try:
                reps = DeepFace.represent(
                    img_path=img_path,
                    model_name=MODEL_NAME,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=True
                )

                if len(reps) > 0:
                    embedding = np.array(reps[0]["embedding"], dtype=np.float32)
                    known_data.append({
                        "name": person_name,
                        "embedding": embedding
                    })
                    print(f"Loaded: {person_name} -> {img_name}")

            except Exception as e:
                print(f"Skipped {img_path}: {e}")

    print("Total known face samples:", len(known_data))
    return len(known_data) > 0

# ---------------------------------------------------
# COSINE DISTANCE
# ---------------------------------------------------
def cosine_distance(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 1.0

    return 1 - (dot / (norm_a * norm_b))

# ---------------------------------------------------
# FIND BEST MATCH
# ---------------------------------------------------
def find_match(face_embedding):
    best_name = "Unknown"
    best_distance = 999.0

    for item in known_data:
        dist = cosine_distance(face_embedding, item["embedding"])

        if dist < best_distance:
            best_distance = dist
            best_name = item["name"]

    if best_distance < THRESHOLD:
        return best_name, best_distance

    return "Unknown", best_distance

# ---------------------------------------------------
# START
# ---------------------------------------------------
if not load_known_faces():
    print("No known faces loaded. Exiting.")
    exit()

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam.")
    exit()

print("Starting recognition... Press Q to quit.")

# ---------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Could not read frame.")
        break

    display_frame = frame.copy()
    frame_count += 1

    if frame_count % FRAME_SKIP == 0:
        current_results = []

        try:
            detections = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=False
            )

            for det in detections:
                area = det.get("facial_area", {})
                x = area.get("x", 0)
                y = area.get("y", 0)
                w = area.get("w", 0)
                h = area.get("h", 0)

                if w <= 0 or h <= 0:
                    continue

                x = max(0, x)
                y = max(0, y)
                x2 = min(frame.shape[1], x + w)
                y2 = min(frame.shape[0], y + h)

                face_crop = frame[y:y2, x:x2]
                if face_crop.size == 0:
                    continue

                reps = DeepFace.represent(
                    img_path=face_crop,
                    model_name=MODEL_NAME,
                    detector_backend="skip",
                    enforce_detection=False
                )

                if len(reps) == 0:
                    continue

                face_embedding = np.array(reps[0]["embedding"], dtype=np.float32)
                name, distance = find_match(face_embedding)

                current_results.append({
                    "x": x,
                    "y": y,
                    "w": x2 - x,
                    "h": y2 - y,
                    "name": name,
                    "distance": distance
                })

        except Exception as e:
            print("Recognition error:", e)

        last_results = current_results

    for item in last_results:
        x = item["x"]
        y = item["y"]
        w = item["w"]
        h = item["h"]
        name = item["name"]
        distance = item["distance"]

        if name == "Unknown":
            color = (0, 0, 255)
            text = f"Unknown ({distance:.2f})"
        else:
            color = (0, 255, 0)
            text = f"Known: {name} ({distance:.2f})"

        cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
        cv2.rectangle(display_frame, (x, y + h - 30), (x + w, y + h), color, cv2.FILLED)
        cv2.putText(display_frame, text, (x + 5, y + h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    cv2.imshow("Known / Unknown Face Recognition", display_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()