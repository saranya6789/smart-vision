from ultralytics import YOLO
import os

# Load the model
model = YOLO('yolov8n.pt') 

# Define the absolute path to your data.yaml
# This prevents the "No such file" error
yaml_path = os.path.abspath("../../Gun-Knife-Thesis/data.yaml")

# Train the model
results = model.train(
    data=yaml_path, 
    epochs=10, 
    imgsz=416, 
    batch=4, 
    name='smart_vision_v1'
)