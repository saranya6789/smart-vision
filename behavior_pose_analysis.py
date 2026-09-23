import cv2
import math
import time
from ultralytics import YOLO

# ---------------------- CONFIG ----------------------
MODEL_PATH = "yolov8n-pose.pt"  # path to YOLOv8 pose model
LOITERING_TIME = 25            # seconds
LOITERING_AREA = 35            # pixels
RUN_CENTER_SPEED = 8
RUN_LEG_SPEED = 10
MAX_HISTORY = 30
MIN_KEYPOINT_CONF = 0.3

# ---------------------- INITIALIZE ----------------------
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

person_data = {}

# ---------------------- UTILS ----------------------
def point_distance(p1, p2):
    if p1 is None or p2 is None:
        return 0
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def get_valid_point(kpts, idx, conf=MIN_KEYPOINT_CONF):
    if idx >= len(kpts): return None
    x, y, c = kpts[idx]
    if c >= conf: return (int(x), int(y))
    return None

def midpoint(p1, p2):
    if not p1 or not p2: return None
    return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)

def get_pose_center(kpts):
    left_hip = get_valid_point(kpts, 11)
    right_hip = get_valid_point(kpts, 12)
    left_shoulder = get_valid_point(kpts, 5)
    right_shoulder = get_valid_point(kpts, 6)
    return midpoint(left_hip, right_hip) or midpoint(left_shoulder, right_shoulder)

def safe_append(lst, val, max_len=MAX_HISTORY):
    lst.append(val)
    if len(lst) > max_len: del lst[0]

def get_leg_speed(lst):
    if len(lst) < 2: return 0
    return point_distance(lst[-1], lst[-2])

# ---------------------- MAIN LOOP ----------------------
while True:
    ret, frame = cap.read()
    if not ret: break
    current_time = time.time()

    results = model.track(frame, persist=True, verbose=False)
    if results and len(results) > 0:
        res = results[0]
        if res.boxes is None or res.keypoints is None: continue
        ids = res.boxes.id.cpu().numpy().astype(int)
        classes = res.boxes.cls.cpu().numpy().astype(int)
        boxes = res.boxes.xyxy.cpu().numpy()
        kpts_data = res.keypoints.data.cpu().numpy()

        for track_id, cls, box, kpts in zip(ids, classes, boxes, kpts_data):
            if cls != 0: continue  # only person

            # get keypoints
            left_shoulder = get_valid_point(kpts, 5)
            right_shoulder = get_valid_point(kpts, 6)
            left_hip = get_valid_point(kpts, 11)
            right_hip = get_valid_point(kpts, 12)
            left_knee = get_valid_point(kpts, 13)
            right_knee = get_valid_point(kpts, 14)
            left_ankle = get_valid_point(kpts, 15)
            right_ankle = get_valid_point(kpts, 16)
            pose_center = get_pose_center(kpts)
            if pose_center is None: continue

            # initialize person
            if track_id not in person_data:
                person_data[track_id] = {
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "centers": [pose_center],
                    "left_knee": [left_knee],
                    "right_knee": [right_knee],
                    "left_ankle": [left_ankle],
                    "right_ankle": [right_ankle],
                    "status": "Normal"
                }
            pdata = person_data[track_id]
            pdata["last_seen"] = current_time
            safe_append(pdata["centers"], pose_center)
            safe_append(pdata["left_knee"], left_knee)
            safe_append(pdata["right_knee"], right_knee)
            safe_append(pdata["left_ankle"], left_ankle)
            safe_append(pdata["right_ankle"], right_ankle)

            time_spent = current_time - pdata["first_seen"]
            center_speed = get_leg_speed(pdata["centers"])
            leg_speed_avg = sum([s for s in [
                get_leg_speed(pdata["left_knee"]),
                get_leg_speed(pdata["right_knee"]),
                get_leg_speed(pdata["left_ankle"]),
                get_leg_speed(pdata["right_ankle"])
            ] if s>0])/4

            # ------------------ Behavior Decision ------------------
            behavior = "Normal"
            if (center_speed>RUN_CENTER_SPEED and leg_speed_avg>RUN_LEG_SPEED) or (leg_speed_avg>RUN_LEG_SPEED+4):
                behavior = "Running"
            if time_spent>=LOITERING_TIME and len(pdata["centers"])>=20:
                recent = pdata["centers"][-20:]
                xs = [p[0] for p in recent if p]
                ys = [p[1] for p in recent if p]
                if max(xs)-min(xs)<LOITERING_AREA and max(ys)-min(ys)<LOITERING_AREA:
                    behavior = "Loitering"
            pdata["status"] = behavior

            # ------------------ Draw ------------------
            x1,y1,x2,y2 = map(int, box)
            color = (0,255,0) if behavior=="Normal" else (0,165,255) if behavior=="Running" else (0,0,255)
            cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
            for pt in [left_shoulder,right_shoulder,left_hip,right_hip,left_knee,right_knee,left_ankle,right_ankle,pose_center]:
                if pt: cv2.circle(frame,pt,4,(255,0,0),-1)
            # skeleton lines
            skeleton = [(left_shoulder,right_shoulder),(left_shoulder,left_hip),(right_shoulder,right_hip),
                        (left_hip,right_hip),(left_hip,left_knee),(left_knee,left_ankle),
                        (right_hip,right_knee),(right_knee,right_ankle)]
            for p1,p2 in skeleton:
                if p1 and p2: cv2.line(frame,p1,p2,color,2)
            # text
            cv2.putText(frame,f"ID:{track_id} Behavior:{behavior}",(x1,y1-20),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)

    cv2.imshow("Behavior Pose Analysis", frame)
    if cv2.waitKey(1) & 0xFF==ord("q"): break

cap.release()
cv2.destroyAllWindows()