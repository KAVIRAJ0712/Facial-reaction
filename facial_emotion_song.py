from flask import Flask, render_template, Response, jsonify
import cv2
from deepface import DeepFace
import random
import webbrowser
import json
import threading

app = Flask(__name__)

# --- CONFIGURATION & SETUP ---

# 1. Load song dataset
try:
    with open("song_links.json", "r", encoding="utf-8") as f:
        songs = json.load(f)
except FileNotFoundError:
    print("WARNING: song_links.json not found. Please run song_fetcher.py first.")
    songs = {}

# 2. Initialize video capture and face detector
cap = None
try:
    # Use 0 for default camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        cap = None # Ensure cap is None if it failed to open
        raise IOError("Cannot open webcam. Please check permissions or camera index.")
except Exception as e:
    print(f"FATAL ERROR initializing camera: {e}")
    cap = None

# Initialize face cascade for fast detection and drawing bounding boxes
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Global flag to prevent multiple songs from playing at once
song_played = False

# --- UTILITY FUNCTIONS ---

def play_song(emotion):
    """Opens a random song URL in the web browser."""
    global song_played
    if emotion in songs and songs[emotion] and not song_played:
        chosen_song = random.choice(songs[emotion])
        print(f"🎶 Playing {emotion.upper()} song: {chosen_song}")
        try:
            webbrowser.open(chosen_song)
            song_played = True
        except Exception as e:
            print(f"Could not open browser: {e}")
            
# --- FLASK ROUTES ---

# Video streaming generator
def gen_frames():
    """Generates frames from the webcam with real-time single-face feedback."""
    if not cap:
        # Return a blank frame with an error message if the camera failed to initialize
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # Mirror the frame for a more natural feel
        frame = cv2.flip(frame, 1)

        # Convert to grayscale and detect faces (fast check for streaming feedback)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # *** UPDATED: Increased sensitivity for better detection ***
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)
        
        # --- Single-Face Check for Real-time Feedback ---
        if len(faces) == 1:
            (x, y, w, h) = faces[0]
            # Draw green rectangle for success
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "READY! Click Analyze", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            # Draw red rectangle(s) for failure
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                
            msg = "NO FACE DETECTED" if len(faces) == 0 else "MULTIPLE FACES! Analysis blocked."
            cv2.putText(frame, msg, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Encode frame and yield
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Video feed route
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Analyze emotion route
@app.route('/analyze', methods=['POST'])
def analyze():
    """Captures a single frame, enforces single-face rule, and analyzes emotion."""
    global song_played
    
    if not cap:
        return jsonify({"error": "Camera not initialized. Check setup."})
        
    ret, frame = cap.read()
    if not ret:
        return jsonify({"error": "Could not capture frame from camera."})
    
    frame = cv2.flip(frame, 1) # Mirror the frame to match the display

    # 1. Detect faces using the fast cascade classifier
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # *** UPDATED: Increased sensitivity for better detection ***
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)

    # 2. **ENFORCE SINGLE-FACE RULE**
    if len(faces) != 1:
        error_msg = "Exactly one face must be visible to analyze the emotion."
        if len(faces) == 0:
            error_msg = "No face detected. Please position yourself in front of the camera."
        return jsonify({"error": error_msg})

    # 3. Proceed with DeepFace analysis (only one face is guaranteed here)
    try:
        # Use the full frame. DeepFace internally re-detects, but our cascade check guarantees one primary subject.
        result = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=True,
            # Using 'opencv' backend in DeepFace is generally reliable and fast, 
            # and works well with our cascade pre-check.
            detector_backend='opencv' 
        )
        
        emotion = result[0]['dominant_emotion'].lower()
        song_played = False
        
        # Play song in a separate thread to keep the web server responsive
        threading.Thread(target=play_song, args=(emotion,)).start()
        
        return jsonify({"emotion": emotion})
        
    except Exception as e:
        # Catch exceptions during the analysis phase (e.g., face detected but not clear enough)
        return jsonify({"error": f"Analysis failed: Could not determine emotion. Please ensure your face is well-lit and clear."})

if __name__ == '__main__':
    # Add use_reloader=False if you encounter camera errors on reload
    app.run(debug=True, threaded=True, use_reloader=False)