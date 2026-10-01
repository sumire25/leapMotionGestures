from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
import cv2

print("Loading FaceLandmarker...")
try:
    face_landmarker = FaceLandmarker.create_from_options(
        FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path="models/face_landmarker.task"),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            output_facial_transformation_matrixes=True,
            output_face_blendshapes=True,
        )
    )
    print("Loaded FaceLandmarker successfully.")
except Exception as e:
    print(f"Error loading FaceLandmarker: {e}")

print("Opening webcam...")
try:
    cap = cv2.VideoCapture(0)
    print(f"Webcam opened: {cap.isOpened()}")
    if cap.isOpened():
        ok, frame = cap.read()
        print(f"Read frame: {ok}")
except Exception as e:
    print(f"Error opening webcam: {e}")
