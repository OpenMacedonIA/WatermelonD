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
        
        # Asegurar que el directorio existe
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
        
        # Tubería (Pipeline) de Optimización
        self.motion_detected = False
        self.face_detected = False
        self.last_frame = None
        
        # Cargar Haar Cascade para detección rápida de rostros
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Tiempos de recarga (Cooldowns)
        self.last_wake_event = 0
        self.wake_cooldown = 10 # Segundos entre eventos de activación

    def start(self):
        if self.running: return
        
        # Probar índice 0, luego 1
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
        """Devuelve True si se detecta movimiento significativo."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.last_frame is None:
            self.last_frame = gray
            return False

        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Comprobar contornos
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        self.last_frame = gray
        
        for c in contours:
            if cv2.contourArea(c) > 500: # Área mínima
                return True
        return False

    def _loop(self):
        while self.running:
            ret, frame = self.video_capture.read()
            if not ret:
                time.sleep(1)
                continue

            # 1. Redimensionar para mayor velocidad (320x240 es suficiente para detección)
            small_frame = cv2.resize(frame, (320, 240))
            
            # 2. Detección de Movimiento (Fase 1)
            if not self._detect_motion(small_frame):
                # ¿No hay movimiento? Dormir más tiempo
                time.sleep(0.5)
                continue
            
            # 3. Detección de Rostros - Haar (Fase 2)
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # ¡Rostro detectado!
                now = time.time()
                if now - self.last_wake_event > self.wake_cooldown:
                    print("Vision: Face detected! Waking up...")
                    self.event_queue.put({'type': 'vision_wake', 'msg': 'User present'})
                    self.last_wake_event = now
                    
                    # 4. Reconocimiento (Fase 3 - Opcional/Limitado por acelerador)
                    # Solo hacemos esto si realmente necesitamos saber QUIÉN es
                    # Por ahora, con despertarse es suficiente para el requisito.
                    # self._identify_user(small_frame)
            
            # Si hay movimiento pero no hay rostro, dormir un poco menos
            time.sleep(0.2)

    def _identify_user(self, frame):
        # Operación pesada, llamar con moderación
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
        Intenta aprender un nuevo rostro a partir del flujo de vídeo actual.
        Devuelve: (éxito, mensaje)
        """
        if not self.video_capture or not self.video_capture.isOpened():
            return False, "Cámara no disponible."

        # Capturar un frame fresco
        ret, frame = self.video_capture.read()
        if not ret:
            return False, "No pude capturar imagen."

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 0:
            return False, "No veo ninguna cara."
        
        if len(face_locations) > 1:
            return False, "Veo demasiadas caras. Ponte tú solo."

        # Generar incrustación (encoding)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if len(face_encodings) > 0:
            encoding = face_encodings[0]
            self.face_db.add_face(name, encoding)
            print(f"Vision: Learned face for {name}")
            return True, f"Cara de {name} guardada correctamente."
            
        return False, "Error al procesar la cara."
