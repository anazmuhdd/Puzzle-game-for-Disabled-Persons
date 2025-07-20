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
    print(f"Error loading Vosk model from '{MODEL_PATH}'. Please ensure it's downloaded and in the correct folder.")
    exit(1)

SAMPLE_RATE = 16000
COMMAND_WORDS = ["left", "right", "up", "down", "rotate", "drop"]
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
        socketio.sleep(0.08) # ~12 FPS to free up CPU

# --- UPDATED: Voice recognition thread with low-latency logic ---
def voice_recognition_thread():
    """Handles live voice recognition with improved responsiveness."""
    print("Starting voice recognition thread...")
    command_sent_this_utterance = False
    
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=None, dtype='int16', channels=1, callback=audio_callback):
            while True:
                data = q.get()
                
                # Check for final result (end of a phrase)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        command = result["text"].strip()
                        print("Final Command:", command)
                        # If we haven't already acted on a partial result,
                        # act on the final one now.
                        if not command_sent_this_utterance and command in COMMAND_WORDS:
                             socketio.emit('voice_command', {'command': command})
                    # Reset the flag for the next spoken phrase
                    command_sent_this_utterance = False
                else:
                    # Check for partial result (while still speaking)
                    partial_result = json.loads(recognizer.PartialResult())
                    if partial_result.get("partial"):
                        partial_text = partial_result["partial"].strip()
                        print(f"Partial: {partial_text}", end='\r')
                        
                        # If we haven't sent a command yet for this phrase
                        # AND the partial text is a valid command word
                        if not command_sent_this_utterance and partial_text in COMMAND_WORDS:
                            print(f"\nActing on partial command: '{partial_text}'")
                            socketio.emit('voice_command', {'command': partial_text})
                            # Set the flag to true so we don't send more commands
                            # for this same spoken phrase (e.g., "left left left")
                            command_sent_this_utterance = True

    except Exception as e:
        print(f"Error in voice recognition thread: {e}")


# --- Flask Routes and WebSocket Events (Unchanged) ---
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