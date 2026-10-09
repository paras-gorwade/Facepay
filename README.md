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

### Day 1 — Computer Vision Foundation

- Webcam capture using OpenCV.
- Real-time face detection.
- Face encoding generation.
- Basic face recognition.
- Registered and unknown face classification.

### Day 2 — Student Face Registration

- Automatic webcam-based face sample collection.
- Multiple face samples per student.
- Local storage of student face images.
- Persistent face encodings using a local pickle file.
- Recognition using stored face encodings.

### Day 3 — Student Database and Wallet Foundation

- Student records table.
- Transaction records table.
- Student registration through a Python script.
- Student lookup using a unique student ID.
- Wallet balance retrieval.
- Database persistence.