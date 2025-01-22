"""This files holds all the configuration settings for flask and flask mail.
They looad sensitive information from environment variables"""

import os


# config.py
class Config:
    SECRET_KEY = 'eatztzghhg'  # For session and flash messages
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes in seconds
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USERNAME = 'floriselectronichealthrecord@gmail.com'  # Gmail account
    MAIL_PASSWORD = 'cxig yqvv cvsn iggc'  # generated App Password
    MAIL_PORT = 465  # Use 465 for SSL
    MAIL_USE_TLS = False  # Setting this to False
    MAIL_USE_SSL = True  # Setting this to true

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'  # Local SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configurations
    PROFILE_PICTURE_FOLDER = os.path.join('static', 'uploads', 'profile_pictures')
    PATIENT_DICOM_FOLDER = os.path.join('static', 'uploads', 'patient_dicom')

    # Allowed extensions for image files
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
