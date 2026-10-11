# FacePay — AI-Powered Contactless Campus Payment System

FacePay is an educational AI/ML project that aims to build a
contactless campus payment prototype using face recognition,
student records, and digital wallet management.

The project combines computer vision, biometric matching,
database management, and transaction processing.

## Project Objectives

The main objectives are:

- Register students using a webcam.
- Detect faces in real time.
- Recognize registered students using face encodings.
- Store multiple face samples per student.
- Maintain student records using SQLite.
- Retrieve student wallet balances.
- Process payments with balance validation.
- Confirm payments using a thumbs-up gesture.
- Maintain transaction history.
- Explore liveness detection and anti-spoofing.
- Evaluate recognition accuracy and system performance.

This project is under active development. Not all planned
features have been implemented.

## Technology Stack

- Python 3.11.9
- OpenCV
- face_recognition
- dlib
- NumPy
- Pillow
- SQLite
- MediaPipe (planned for gesture recognition)

## Current Features


## Development Progress

| Day | Completed Work |
|---|---|
| Day 1 | Webcam capture, face detection, and basic recognition |
| Day 2 | Student registration and multiple face samples |
| Day 3 | SQLite database, student records, and wallet lookup |
| Day 4 | Database lookup optimization and automated testing |
| Day 5 | Wallet migration, payment processing, and transaction testing |