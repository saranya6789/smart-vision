import cv2
import os
import numpy as np

# ------------------------
# Known Faces Directory
# ------------------------
known_faces_dir = r"C:\Users\saran\OneDrive\Desktop\SmartVision\Known_Faces"

if not hasattr(cv2, "face"):
    print("cv2.face module not found. Install opencv-contrib-python")
    exit()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
label_dict = {}
current_label = 0

# ------------------------
# Load known faces
# ------------------------
for person_name in os.listdir(known_faces_dir):
    person_folder = os.path.join(known_faces_dir, person_name)
    if not os.path.isdir(person_folder):
        continue

    label_dict[current_label] = person_name

    for img_name in os.listdir(person_folder):
        img_path = os.path.join(person_folder, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print("Skipping invalid image:", img_path)
            continue

        face = cv2.resize(img, (200, 200))
        faces.append(face)
        labels.append(current_label)

    current_label += 1

if len(faces) == 0:
    print("No valid known face images found.")
    exit()

faces = np.array(faces)
labels = np.array(labels)

# ------------------------
# Train recognizer
# ------------------------
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, labels)
print("Known faces loaded and recognizer trained.")

# ------------------------
# Start camera
# ------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot access camera")
    exit()

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in detected_faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_gray = cv2.resize(roi_gray, (200, 200))

        try:
            label, confidence = recognizer.predict(roi_gray)
            if confidence < 70:
                name = label_dict[label]
            else:
                name = "Unknown"
        except Exception:
            name = "Unknown"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("AI Surveillance", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()