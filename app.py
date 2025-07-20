from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import mediapipe as mp
import base64
import vosk
import sounddevice as sd
import queue
import json
import threading

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Head Tracking Setup (Unchanged) ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
LEFT_THRESHOLD, RIGHT_THRESHOLD = 0.43, 0.58
UP_THRESHOLD, DOWN_THRESHOLD = 0.40, 0.60

# --- Voice Recognition Setup ---
q = queue.Queue()
MODEL_PATH = "vosk-model-small-en-us-0.15"
try:
    model = vosk.Model(MODEL_PATH)
except Exception as e:
    print(f"Error loading Vosk model from '{MODEL_PATH}'.")
    exit(1)

SAMPLE_RATE = 16000

# --- NEW: Define a specific list of words for the recognizer ---
# This makes recognition much more accurate for our specific use case.
COMMAND_WORDS = ["left", "right", "up", "down", "rotate", "drop"]

# --- MODIFIED: Pass the command words to the recognizer ---
recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE, json.dumps(COMMAND_WORDS))


def audio_callback(indata, frames, time, status):
    if status: print(status, flush=True)
    q.put(bytes(indata))

# --- Background Threads ---
threads_started = threading.Event()

def video_processing_thread():
    cap = cv2.VideoCapture(0)
    print("Starting video processing thread...")
    while cap.isOpened():
        success, image = cap.read()
        if not success: continue
        image = cv2.flip(image, 1)
        image.flags.writeable = False; image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB); results = face_mesh.process(image_rgb); image.flags.writeable = True
        status = "Center"
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            nose_x, nose_y = landmarks[1].x, landmarks[1].y
            if nose_x < LEFT_THRESHOLD: status = "Tilted Left"
            elif nose_x > RIGHT_THRESHOLD: status = "Tilted Right"
            elif nose_y < UP_THRESHOLD: status = "Tilted Up"
            elif nose_y > DOWN_THRESHOLD: status = "Tilted Down"
        cv2.putText(image, f"Status: {status}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        _, buffer = cv2.imencode('.jpg', image)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_feed', {'image': jpg_as_text})
        socketio.emit('control_command', {'action': status})
        # Optional: Increase sleep time slightly to give more CPU time to the audio thread
        socketio.sleep(0.08) # Roughly 12 FPS

def voice_recognition_thread():
    print("Starting voice recognition thread...")
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=None, dtype='int16', channels=1, callback=audio_callback):
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        command = result["text"]
                        print("Voice Command Detected:", command)
                        socketio.emit('voice_command', {'command': command})
    except Exception as e:
        print(f"Error in voice recognition thread: {e}")

# --- Flask Routes and WebSocket Events ---
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global threads_started
    print('Client connected!')
    if not threads_started.is_set():
        print("Starting background threads for video and voice.")
        socketio.start_background_task(target=video_processing_thread)
        socketio.start_background_task(target=voice_recognition_thread)
        threads_started.set()

if __name__ == '__main__':
    print("Starting Flask-SocketIO server.")
    print("Access the game at http://<YOUR-LOCAL-IP>:5000")
    socketio.run(app, host='0.0.0.0', port=5000)