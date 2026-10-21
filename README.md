# FacePay — AI-Powered Contactless Campus Payment System

FacePay is an educational AI/ML project that demonstrates a contactless campus payment prototype using facial recognition, student records, and digital wallet management.

The project combines computer vision, biometric matching, database management, and transaction processing.

## Project Objectives

* Register students using a webcam.
* Detect and recognize registered faces in real time.
* Store multiple face samples per student.
* Manage student records using SQLite.
* Retrieve and manage student wallet balances.
* Process payments with balance validation.
* Verify payments using a 4-digit PIN.
* Confirm payments using a thumbs-up gesture.
* Maintain transaction history.
* Explore liveness detection and anti-spoofing.
* Evaluate recognition accuracy and system performance.

## Technology Stack

* Python 3.11.9
* OpenCV
* face_recognition
* dlib
* NumPy
* Pillow
* MediaPipe
* SQLite

## Development Progress

| Day   | Completed Work                                                                     |
| ----- | ---------------------------------------------------------------------------------- |
| Day 1 | Webcam capture, face detection, and basic face recognition                         |
| Day 2 | Student registration and multiple face samples                                     |
| Day 3 | SQLite database, student records, and wallet lookup                                |
| Day 4 | Database lookup optimization and automated testing                                 |
| Day 5 | Wallet migration, payment processing, and transaction testing                      |
| Day 6 | MediaPipe hand tracking and thumbs-up gesture confirmation                         |
| Day 7 | 4-digit PIN verification, payment-flow integration, and end-to-end payment testing |

## Payment Workflow

1. Recognize the registered student.
2. Enter the payment amount.
3. Validate the wallet balance.
4. Verify the 4-digit PIN.
5. Confirm the payment using a thumbs-up gesture.
6. Process the transaction and update the wallet balance.
7. Display the payment result and transaction details.

## Disclaimer

FacePay is an educational project developed for learning and portfolio purposes. It is a prototype and is not a production-ready payment system.
