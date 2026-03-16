import cv2
import numpy as np
import sqlite3
import time
from ultralytics import YOLO
from insightface.app import FaceAnalysis
import pickle
import json
import colorama
import os  # < Added Import
from thefuzz import process


class Vision_Pro:
    def __init__(self):
        print('Initializing Vision Pro Engine...')
        self.yolo = YOLO('yolov8n.pt')
        self.is_running = True

        self.app = FaceAnalysis(
            name='buffalo_s',
            root='C:/Users/priya/.insightface',
            providers=['CUDAExecutionProvider']
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))

        self.conn = sqlite3.connect('vision_pro.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.setup_db()

        #  🚀 NEW FEATURE: Auto-Import from Folder 
        self.import_from_folder()


        self.known_names = []
        self.known_embeddings = []
        self.known_info = []
        self.load_memory()

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        print('Vision Pro Engine Ready.')

    def import_from_folder(self):
        """
        Scans 'known_faces' folder.
        If you put 'ankit.jpg' there, it automatically registers 'Ankit' into the DB.
        """
        folder_path = "known_faces"

        # Create folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(
                colorama.Fore.YELLOW + f"📁 Created '{folder_path}' folder. Drop photos here (e.g. 'Ankit.jpg') to auto-register!")
            return

        print(colorama.Fore.CYAN + "📂 Scanning 'known_faces' folder for new people...")

        valid_extensions = ('.jpg', '.jpeg', '.png')
        new_count = 0

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(valid_extensions):
                # Clean name: "ankit_dandotia.jpg" -> "Ankit Dandotia"
                name = os.path.splitext(filename)[0].replace("_", " ").title()

                # Check if already exists in DB (Prevent Duplicates)
                self.cursor.execute("SELECT 1 FROM humans WHERE name = ?", (name,))
                if self.cursor.fetchone():
                    continue  # Skip if already registered

                # Process Image
                img_path = os.path.join(folder_path, filename)
                img = cv2.imread(img_path)

                if img is None:
                    continue

                # InsightFace requires RGB
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                faces = self.app.get(rgb_img)

                if len(faces) == 0:
                    print(f"⚠️ Warning: No face found in {filename}. Skipping.")
                    continue

                # Take the largest face in the image
                face = sorted(faces, key=lambda x: x.bbox[2] * x.bbox[3])[-1]
                embedding = face.embedding

                # Prepare DB Entry
                binary_enc = pickle.dumps(embedding)
                info = json.dumps({"details": "Imported from file", "added_on": time.strftime("%Y-%m-%d")})

                # Insert into DB (4 Times to match the structure expected by other functions if needed, or just 1 is fine usually, but let's stick to 1 for import)
                # Note: The original register_face adds 4 entries (front, left, right, smile).
                # For file import, we usually have only 1. We will add it once.

                try:
                    self.cursor.execute("INSERT INTO humans (name, embedding, info) VALUES (?, ?, ?)",
                                        (name, binary_enc, info))
                    new_count += 1
                    print(f"✅ Auto-Registered: {name}")
                except Exception as e:
                    print(f"❌ Error importing {name}: {e}")

        if new_count > 0:
            self.conn.commit()
            print(colorama.Fore.GREEN + f"🎉 Imported {new_count} new faces from folder!")
        else:
            print("Folder check complete. No new valid images found.")

    def setup_db(self):
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS humans
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                name
                TEXT,
                info
                TEXT,
                embedding
                BLOB
            )
            ''')
        self.conn.commit()

    def load_memory(self):
        print(colorama.Fore.CYAN + 'Loading Vision Pro Memory...')
        self.cursor.execute("SELECT name, embedding, info FROM humans")
        rows = self.cursor.fetchall()

        self.known_info = []
        self.known_names = []
        self.known_embeddings = []

        for name, enc_blob, info_json in rows:
            embedding = pickle.loads(enc_blob)
            try:
                info = json.loads(info_json) if info_json else {}
            except:
                info = {}

            self.known_names.append(name)
            self.known_embeddings.append(embedding)
            self.known_info.append(info)

        print(colorama.Fore.GREEN + f"[Vision] Loaded {len(self.known_names)} identities.")

    def register_face(self, frame, name, info_dict, tts_engine):
        # (Keeping your original manual registration logic here unchanged)
        def speak_and_wait(text, wait_for_user_seconds=0):
            if tts_engine:
                tts_engine.speak(text)
                time.sleep(0.5)
                while hasattr(tts_engine, '_is_speaking') and tts_engine._is_speaking:
                    time.sleep(0.1)
            else:
                print(f"[TTS MISSING]: {text}")
            if wait_for_user_seconds > 0:
                print(f"Waiting {wait_for_user_seconds}s for user action...")
                time.sleep(wait_for_user_seconds)

        import os
        folder_path = "registered_faces"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        clean_name = name.replace(" ", "_").lower()
        timestamp = int(time.time())

        # 1. FRONT FACE
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.app.get(rgb_frame)
        if len(faces) == 0:
            print(f'No faces detected')
            speak_and_wait("I can't see your face. Please look at the camera.", 0)
            return False

        speak_and_wait("Hold on, capturing front view.", 0)
        face_straight = sorted(faces, key=lambda x: x.bbox[2] * x.bbox[3])[-1]
        embedding_straight = face_straight.embedding
        cv2.imwrite(f"{folder_path}/{clean_name}_front_{timestamp}.jpg", frame)

        # 2. LEFT FACE
        speak_and_wait("Now turn your face slightly to the left.", wait_for_user_seconds=3)
        ret, frame_left = self.cap.read()
        if not ret: return False
        rgb_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2RGB)
        faces_left = self.app.get(rgb_left)
        if len(faces_left) == 0:
            speak_and_wait("Face not found in left view, using front view instead.", 0)
            embedding_left = embedding_straight
        else:
            face_left_obj = sorted(faces_left, key=lambda x: x.bbox[2] * x.bbox[3])[-1]
            embedding_left = face_left_obj.embedding
            cv2.imwrite(f"{folder_path}/{clean_name}_left_{timestamp}.jpg", frame_left)

        # 3. RIGHT FACE
        speak_and_wait("Now turn slightly to the right.", wait_for_user_seconds=3)
        ret, frame_right = self.cap.read()
        if not ret: return False
        rgb_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2RGB)
        faces_right = self.app.get(rgb_right)
        if len(faces_right) == 0:
            speak_and_wait("Face not found in right view, using front view instead.", 0)
            embedding_right = embedding_straight
        else:
            face_right_obj = sorted(faces_right, key=lambda x: x.bbox[2] * x.bbox[3])[-1]
            embedding_right = face_right_obj.embedding
            cv2.imwrite(f"{folder_path}/{clean_name}_right_{timestamp}.jpg", frame_right)

        # 4. SMILE
        speak_and_wait("Okay, now look at the camera and give me a big smile.", wait_for_user_seconds=2)
        ret, frame_smile = self.cap.read()
        embedding_smile = embedding_straight
        if ret:
            rgb_smile = cv2.cvtColor(frame_smile, cv2.COLOR_BGR2RGB)
            faces_smile = self.app.get(rgb_smile)
            if len(faces_smile) > 0:
                face_smile_obj = sorted(faces_smile, key=lambda x: x.bbox[2] * x.bbox[3])[-1]
                embedding_smile = face_smile_obj.embedding

        # DB Insertion
        json_info = json.dumps(info_dict)
        binary_enc_straight = pickle.dumps(embedding_straight)
        binary_enc_left = pickle.dumps(embedding_left)
        binary_enc_right = pickle.dumps(embedding_right)
        binary_enc_smile = pickle.dumps(embedding_smile)

        query = "INSERT INTO humans (name, embedding, info) VALUES (?, ?, ?)"
        self.cursor.execute(query, (name, binary_enc_straight, json_info))
        self.cursor.execute(query, (name, binary_enc_left, json_info))
        self.cursor.execute(query, (name, binary_enc_right, json_info))
        self.cursor.execute(query, (name, binary_enc_smile, json_info))
        self.conn.commit()

        self.known_embeddings.extend([embedding_straight, embedding_left, embedding_right, embedding_smile])
        self.known_names.extend([name, name, name, name])
        self.known_info.extend([info_dict, info_dict, info_dict, info_dict])

        speak_and_wait(f"Done! I have successfully registered {name}.", 0)
        print(colorama.Fore.GREEN + f"[Vision] Registered new face: {name}")
        return True

    def recognize(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.app.get(rgb_frame)

        recognized = []
        for face in faces:
            embedding = face.embedding
            name = "Unknown"
            info = {}
            max_score = 0.0

            if len(self.known_embeddings) > 0:
                known_matrix = np.array(self.known_embeddings)
                sims = np.dot(known_matrix, embedding) / (
                        np.linalg.norm(known_matrix, axis=1) * np.linalg.norm(embedding)
                )
                best_idx = np.argmax(sims)
                max_score = sims[best_idx]

                if max_score > 0.4:
                    name = self.known_names[best_idx]
                    info = self.known_info[best_idx]

            bbox = face.bbox.astype(int)
            recognized.append({
                'name': name,
                'info': info,
                'bbox': bbox,
                'score': float(max_score)
            })

        return recognized

    def close_camera(self):
        self.is_running = False
        time.sleep(0.1)
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        print("Camera Resource Released.")

    def scan_scene(self):
        ret, frame = self.cap.read()
        if not ret:
            return ["Camera Error"]
        results = self.recognize(frame)
        if not results:
            return []
        found_names = []
        for face in results:
            found_names.append(face['name'])
        return found_names

    def get_info(self, name_query):
        # (Same as before)
        try:
            self.cursor.execute("SELECT name, info FROM humans WHERE name LIKE ?", (name_query,))
            row = self.cursor.fetchone()
            if row:
                return row[0], json.loads(row[1])
            return None
        except Exception:
            return None


if __name__ == "__main__":
    v = Vision_Pro()

    print("\n TEST MODE: Press 'q' to quit ")
    print("1. If you added photos in 'known_faces', they are imported now.")
    print("2. The camera will now try to recognize you.")

    while True:
        ret, frame = v.cap.read()
        if not ret: break

        detections = v.recognize(frame)

        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            name = d['name']
            score = d['score']

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{name} ({int(score * 100)}%)"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("Vision Pro Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    v.close_camera()