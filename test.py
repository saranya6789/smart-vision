import cv2
print("OpenCV version:", cv2.__version__)

if hasattr(cv2, 'face') and hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
    print("LBPHFaceRecognizer is available ✅")
else:
    print("LBPHFaceRecognizer not found ❌")