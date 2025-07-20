import cv2
import mediapipe as mp

# --- INITIALIZATION ---
# Initialize MediaPipe Face Mesh solution
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# Initialize OpenCV's video capture for the webcam
cap = cv2.VideoCapture(0) # 0 is the default webcam

# Set thresholds for movement detection
# A value < LEFT_THRESHOLD is a left tilt.
# A value > RIGHT_THRESHOLD is a right tilt.
# The space between them is a "dead zone" to prevent jitter.
LEFT_THRESHOLD = 0.43
RIGHT_THRESHOLD = 0.58

with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as face_mesh:

    print("Starting webcam feed. Press 'q' to quit.")

    # --- MAIN LOOP ---
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # To improve performance, mark the image as not writeable to pass by reference.
                # To improve performance, mark the image as not writeable to pass by reference.
        image.flags.writeable = False
        # Convert the BGR image to RGB.
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Process the image and find face landmarks.
        results = face_mesh.process(image_rgb)

        # Re-enable writing to the image to draw on it.
        image.flags.writeable = True
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        status = "No Face Detected"

        # --- MOVEMENT LOGIC ---
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                
                # We use the nose tip (landmark index 1) as our main reference point.
                # The coordinates are normalized (from 0.0 to 1.0).
                nose_tip = face_landmarks.landmark[1]
                nose_x_position = nose_tip.x
                
                # Check the nose position against our thresholds.
                if nose_x_position < LEFT_THRESHOLD:
                    status = "Tilted Left"
                elif nose_x_position > RIGHT_THRESHOLD:
                    status = "Tilted Right"
                else:
                    status = "Center"

                # Draw the face mesh annotations on the image for visual feedback.
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=drawing_spec)

        # Display the status text on the image.
        cv2.putText(
            image,
            f"Status: {status}",
            (50, 50), # Position on screen
            cv2.FONT_HERSHEY_SIMPLEX,
            1, # Font scale
            (0, 255, 0), # Text color (Green)
            2, # Thickness
            cv2.LINE_AA
        )

        # Show the final image.
        cv2.imshow('Head Movement Detection', image)

        # Exit loop if 'q' is pressed.
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# --- CLEANUP ---
cap.release()
cv2.destroyAllWindows()
print("Script finished.")