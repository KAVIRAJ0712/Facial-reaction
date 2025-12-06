import cv2

# Load face detector (Haar Cascade is fast but sometimes less accurate than CNNs)
# This file is typically included with OpenCV installations.
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Initialize the webcam (Camera Index 0)
# cv2.CAP_DSHOW is often used on Windows for better compatibility/speed.
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Check if the camera opened successfully
if not cap.isOpened():
    raise RuntimeError("Cannot open webcam. Check camera permissions or index.")

while True:
    # 1. Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break # Exit the loop if frame capture fails
    
    # 2. Convert to grayscale for faster face detection (Haar cascades work on grayscale)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 3. Detect faces in the grayscale image
    # The result is a list of (x, y, w, h) rectangles
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    # 4. Control Logic: Check the number of detected faces
    if len(faces) == 1:
        # **Case 1: Exactly One Face Detected (Allowed for processing)**
        (x, y, w, h) = faces[0]
        
        # Draw a GREEN rectangle around the single face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Crop the single face region (ready for emotion analysis)
        single_face = frame[y:y + h, x:x + w]

        # Display status message in GREEN
        cv2.putText(
            frame,
            "✅ PROCESSING SINGLE FACE",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0), # Green color
            2,
        )

        # 👉 You would insert your DeepFace.analyze(single_face, ...) code here
        
    else:
        # **Case 2: Zero or Multiple Faces Detected (Processing Blocked)**
        
        # Determine the error message
        msg = "❌ NO FACE DETECTED" if len(faces) == 0 else "❌ MULTIPLE FACES! Analysis Blocked."
        
        # Draw RED rectangles around any detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Display error message in RED
        cv2.putText(
            frame,
            msg,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255), # Red color
            2,
        )

    # 5. Display the resulting frame
    cv2.imshow("Facial Emotion Detector", frame)

    # 6. Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup resources
cap.release()
cv2.destroyAllWindows()