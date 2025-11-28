from flask import Flask, render_template, Response, jsonify
import cv2
from deepface import DeepFace
import random
import webbrowser
import json
import threading

app = Flask(__name__)

# Load song dataset
with open("song_links.json", "r", encoding="utf-8") as f:
    songs = json.load(f)

cap = cv2.VideoCapture(0)
song_played = False

# Function to play YouTube song
def play_song(emotion):
    global song_played
    if emotion in songs and songs[emotion] and not song_played:
        chosen_song = random.choice(songs[emotion])
        print(f"🎶 Playing {emotion} song: {chosen_song}")
        webbrowser.open(chosen_song)
        song_played = True

# Video streaming generator
def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
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
    global song_played
    ret, frame = cap.read()
    if not ret:
        return jsonify({"error": "Could not capture frame"})
    try:
        # Fast emotion detection using OpenCV backend
        result = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=True,
            detector_backend='opencv'  # lightweight and faster
        )
        emotion = result[0]['dominant_emotion'].lower()
        song_played = False
        threading.Thread(target=play_song, args=(emotion,)).start()
        return jsonify({"emotion": emotion})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
