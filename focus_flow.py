import cv2
import time
import math
import numpy as np
import pyautogui
import mediapipe as mp

# CONFIGURATION 
CAM_WIDTH, CAM_HEIGHT = 640, 480
LOOK_LEFT_THRESHOLD = -15
LOOK_RIGHT_THRESHOLD = 15
STABILITY_FRAMES = 10 
COOLDOWN = 1.0 

# SETUP MEDIA PIPE 
try:
    # Classes which returs Face and hand landmarks
    mp_face_mesh = mp.solutions.face_mesh
    mp_hands = mp.solutions.hands
    
    # Helps in drawing the landmarks on image
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
except AttributeError:
    print("Error: MediaPipe version incompatibility.")
    exit()

# MAIN EXECUTION 
cap = cv2.VideoCapture(0)
cap.set(3, CAM_WIDTH)
cap.set(4, CAM_HEIGHT)

is_paused = False 
last_state_change_time = 0
looking_away_counter = 0 

print("FocusFlow is Active. Open YouTube/VLC and minimize this window.")

with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
     mp_hands.Hands(model_complexity=0, max_num_hands=1) as hands:

    while cap.isOpened():
        success, image = cap.read()
        if not success: continue

        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        face_results = face_mesh.process(image_rgb)
        hand_results = hands.process(image_rgb)

        image.flags.writeable = True
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        h, w, c = image.shape

        # FEATURE 1: HEAD POSE DETECTION
        currently_looking_away = False
        status_text = "Focused"
        
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                face_3d = []
                face_2d = []
                
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx in [33, 263, 1, 61, 291, 199]:
                        x, y = int(lm.x * w), int(lm.y * h)
                        face_2d.append([x, y])
                        face_3d.append([x, y, lm.z])
                
                face_2d = np.array(face_2d, dtype=np.float64)
                face_3d = np.array(face_3d, dtype=np.float64)

                focal_length = 1 * w
                cam_matrix = np.array([[focal_length, 0, w / 2],
                                       [0, focal_length, h / 2],
                                       [0, 0, 1]])
                dist_matrix = np.zeros((4, 1), dtype=np.float64)

                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
                rmat, jac = cv2.Rodrigues(rot_vec)

                # Modern OpenCV Unpacking
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

                y_angle = angles[1] * 360 

                if y_angle < LOOK_LEFT_THRESHOLD:
                    status_text = "Looking Left"
                    currently_looking_away = True
                elif y_angle > LOOK_RIGHT_THRESHOLD:
                    status_text = "Looking Right"
                    currently_looking_away = True
                else:
                    status_text = "Focused"
                    currently_looking_away = False
                
                cv2.putText(image, f"Head: {int(y_angle)}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            status_text = "Absent"
            currently_looking_away = True

        # STABILITY BUFFER 
        if currently_looking_away:
            looking_away_counter += 1
        else:
            looking_away_counter = 0

        trigger_action = looking_away_counter > STABILITY_FRAMES
        
        # PAUSE/PLAY TRIGGER
        current_time = time.time()
        if (current_time - last_state_change_time) > COOLDOWN:
            if trigger_action and not is_paused:
                pyautogui.press('playpause')
                is_paused = True
                last_state_change_time = current_time
                print("Action: PAUSED")
            elif not trigger_action and is_paused:
                pyautogui.press('playpause')
                is_paused = False
                last_state_change_time = current_time
                print("Action: PLAYING")

        # FEATURE 2: VOLUME CONTROL 
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                x1, y1 = int(thumb.x * w), int(thumb.y * h)
                x2, y2 = int(index.x * w), int(index.y * h)
                
                # Visuals
                cv2.line(image, (x1, y1), (x2, y2), (255, 0, 255), 3)
                length = math.hypot(x2 - x1, y2 - y1)
                
                # LOGIC FOR ZONES 
                # < 50px = Volume Down Zone
                # > 180px = Volume Up Zone
                # 50-180px = Stable Zone (Do nothing)
                
                if length < 50:
                    cv2.putText(image, "VOL DOWN", (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    pyautogui.press('volumedown')
                    
                elif length > 180:
                    cv2.putText(image, "VOL UP", (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    pyautogui.press('volumeup')
                else:
                    cv2.putText(image, "VOL STABLE", (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Show Output
        cv2.putText(image, f"State: {'PAUSED' if is_paused else 'PLAYING'}", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow('FocusFlow', image)

        if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()