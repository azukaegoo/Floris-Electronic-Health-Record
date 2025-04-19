# Floris Electronic Health Record (EHR) System

## Introduction
The Floris EHR System is a user-friendly and efficient platform designed to simplify healthcare management for doctors and other healthcare professionals. Built with secure backend technology and a local SQLite database, it ensures safe and effective management of patient records. Its primary goal is to enhance productivity and improve the quality of patient care by providing essential features without unnecessary complexity.

## Features

1. **Patient Management**
   - Add, view, edit, and delete patient personal details, emergency contacts, and clinical records.
   - Role-based access ensures doctors can only manage patients they have added.

2. **Clinical Forms**
   - Modular forms for vital signs, medical history, medication, laboratory tests, radiology, and billing.
   - Doctors can choose necessary forms and save them to the database.

3. **Radiology Records**
   - Upload and manage radiology images in formats like PNG, JPEG

4. **Security and Authentication**
   - Secure password management using hashed passwords.
   - Role-based dashboard access ensures data privacy.

5. **Emergency Contact Management**
   - Add one emergency contact per patient using a simple one-to-one relationship model.

6. **Simplified Workflow**
   - Clear flow from registration to patient record management.
   - Integrated dashboards for seamless account and data management.

## Technical Architecture

- **Backend**: Flask framework with Flask-Login for authentication and Flask-SQLAlchemy for database handling.
- **Database**: Local SQLite database for storing user, patient, clinical, and radiology data.
- **File Upload**: Supports profile pictures, radiology images previews.
- **Security**: Password hashing with Werkzeug and secure database queries.
- **Design**: Clean modular architecture for scalability.

## Installation and Setup

- **Prerequisites**:
  - Python 3.11+
  - Required Python dependencies (listed in `requirements.txt`).
  - 


Note the return repeated query record filter for all patient clinical route is not a redundancy but done purposely because the tabs
are alternated from route, removing repeated query will cause the record
not to display when alternating between tabs