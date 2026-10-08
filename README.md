# FacePay

AI-powered contactless campus payment system using face recognition.

## Project Overview

FacePay is a computer vision based campus payment system designed to provide a fast and contactless payment experience.

The system identifies a registered student using facial recognition and will later connect the identified student to a digital wallet and payment transaction system.

## Current Development Status

### Day 1 - Face Recognition Foundation
- Webcam capture using OpenCV
- Real-time face detection
- Face encoding generation
- Face recognition
- Unknown face detection

### Day 2 - Student Registration
- Automatic student registration
- Multiple face samples per student
- 7 face encodings per registered student
- Student-specific face image folders
- Persistent face encoding storage
- Multiple student recognition
- Unknown person detection

## Current System Flow

```text
Webcam
   ↓
Face Detection
   ↓
Face Encoding
   ↓
Compare with Registered Encodings
   ↓
Student Identification
   ↓
Paras / Other Registered Student / Unknown