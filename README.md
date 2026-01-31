# FocusFlow

Attention-aware media controller using Computer Vision.

## Overview
FocusFlow automatically pauses media when the user looks away and resumes playback when attention is restored.

## Features
- Auto Pause/Play based on head pose
- Gesture-based volume control
- Real-time processing using webcam
- Works with YouTube, VLC, Spotify

## Technologies Used
- Python
- OpenCV
- MediaPipe
- PyAutoGUI

## How It Works
1. Webcam captures live video frames
2. Face landmarks are detected
3. Head pose is estimated
4. Media is paused or resumed based on attention
5. Hand gestures control volume

## Project Structure
- `focus_flow.py` – core application
- `requirements.txt` – dependencies
- `README.md` – documentation

## Future Scope
- Eye gaze tracking
- Additional gestures
- Cross-platform support


