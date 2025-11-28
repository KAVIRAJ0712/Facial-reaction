import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    raise RuntimeError("Cannot open webcam. Check camera permissions or index.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        continue
    cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
