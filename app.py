from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import mediapipe as mp
import base64

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- MediaPipe and Threshold Setup ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# --- Define all thresholds ---
LEFT_THRESHOLD = 0.43
RIGHT_THRESHOLD = 0.58
# Y-coordinates are smaller at the top, larger at the bottom
UP_THRESHOLD = 0.40  # Adjust as needed
DOWN_THRESHOLD = 0.60 # Adjust as needed


def video_processing_thread():
    cap = cv2.VideoCapture(0)
    print("Starting video processing thread...")
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)
        image.flags.writeable = True

        status = "Center" # Default status

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            nose = landmarks[1] # Using nose tip (landmark 1)
            nose_x = nose.x
            nose_y = nose.y
            
            # --- UPDATED: Control logic now includes vertical checks ---
            # Prioritize Left/Right movement
            if nose_x < LEFT_THRESHOLD:
                status = "Tilted Left"
            elif nose_x > RIGHT_THRESHOLD:
                status = "Tilted Right"
            # Only check for Up/Down if not tilted sideways
            elif nose_y < UP_THRESHOLD:
                status = "Tilted Up"
            elif nose_y > DOWN_THRESHOLD:
                status = "Tilted Down"

        cv2.putText(image, f"Status: {status}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        
        _, buffer = cv2.imencode('.jpg', image)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('video_feed', {'image': jpg_as_text})
        socketio.emit('control_command', {'action': status})
        
        socketio.sleep(0.05)


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected!')
    socketio.start_background_task(target=video_processing_thread)

if __name__ == '__main__':
    print("Starting Flask-SocketIO server.")
    print("Access the game at http://<YOUR-LOCAL-IP>:5000")
    socketio.run(app, host='0.0.0.0', port=5000)