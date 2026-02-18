import cv2
import face_recognition
import json
import os
import threading
import time
import numpy as np

class FaceDB:
    def __init__(self, db_path='config/faces.json'):
        self.db_path = db_path
        self.known_face_encodings = []
        self.known_face_names = []
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    for name, encoding in data.items():
                        self.known_face_names.append(name)
                        self.known_face_encodings.append(np.array(encoding))
            except Exception as e:
                print(f"Error loading face DB: {e}")

    def save_db(self):
        data = {}
        for name, encoding in zip(self.known_face_names, self.known_face_encodings):
            data[name] = encoding.tolist()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f)

    def add_face(self, name, encoding):
        self.known_face_names.append(name)
        self.known_face_encodings.append(encoding)
        self.save_db()

class VisionManager:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.face_db = FaceDB()
        
        self.running = False
        self.thread = None
        self.video_capture = None
        
        # Optimization Pipeline
        self.motion_detected = False
        self.face_detected = False
        self.last_frame = None
        
        # Load Haar Cascade for fast face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Cooldowns
        self.last_wake_event = 0
        self.wake_cooldown = 10 # Seconds between wake events

    def start(self):
        if self.running: return
        
        # Try index 0, then 1
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            self.video_capture = cv2.VideoCapture(1)
            
        if not self.video_capture.isOpened():
            print("Could not open video device.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("VisionManager started (Low Resource Mode).")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.video_capture:
            self.video_capture.release()

    def _detect_motion(self, frame):
        """Returns True if significant motion is detected."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.last_frame is None:
            self.last_frame = gray
            return False

        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Check for contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        self.last_frame = gray
        
        for c in contours:
            if cv2.contourArea(c) > 500: # Minimum area
                return True
        return False

    def _loop(self):
        while self.running:
            ret, frame = self.video_capture.read()
            if not ret:
                time.sleep(1)
                continue

            # 1. Resize for speed (320x240 is enough for detection)
            small_frame = cv2.resize(frame, (320, 240))
            
            # 2. Motion Detection (Stage 1)
            if not self._detect_motion(small_frame):
                # No motion? Sleep longer
                time.sleep(0.5)
                continue
            
            # 3. Face Detection - Haar (Stage 2)
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Face detected!
                now = time.time()
                if now - self.last_wake_event > self.wake_cooldown:
                    print("Vision: Face detected! Waking up...")
                    self.event_queue.put({'type': 'vision_wake', 'msg': 'User present'})
                    self.last_wake_event = now
                    
                    # 4. Recognition (Stage 3 - Optional/Throttled)
                    # We only do this if we really need to know WHO it is
                    # For now, just waking up is enough for the requirement.
                    # self._identify_user(small_frame)
            
            # If motion but no face, sleep a bit less
            time.sleep(0.2)

    def _identify_user(self, frame):
        # Heavy operation, call sparingly
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.face_db.known_face_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = self.face_db.known_face_names[first_match_index]
            
            print(f"Vision: Identified {name}")
            self.event_queue.put({'type': 'vision_identify', 'name': name})

    def learn_user(self, name):
        """
        Attempts to learn a new face from the current video stream.
        Returns: (success, message)
        """
        if not self.video_capture or not self.video_capture.isOpened():
            return False, "Cámara no disponible."

        # Capture a fresh frame
        ret, frame = self.video_capture.read()
        if not ret:
            return False, "No pude capturar imagen."

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 0:
            return False, "No veo ninguna cara."
        
        if len(face_locations) > 1:
            return False, "Veo demasiadas caras. Ponte tú solo."

        # Generate encoding
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if len(face_encodings) > 0:
            encoding = face_encodings[0]
            self.face_db.add_face(name, encoding)
            print(f"Vision: Learned face for {name}")
            return True, f"Cara de {name} guardada correctamente."
            
        return False, "Error al procesar la cara."
