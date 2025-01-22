from flask import Flask
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager
from ehr_system.config import Config
from ehr_system.models import db, UserDoctor
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
mail = Mail(app)
ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize Flask-Login for user session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to 'login' route if user is not authenticated

# Initialize SQLAlchemy
db.init_app(app)
with app.app_context():
    db.create_all()


# Set up login manager
@login_manager.user_loader
def load_user(user_id):
    return UserDoctor.query.get(int(user_id))


# Ensure the upload folders exist
os.makedirs(app.config['PROFILE_PICTURE_FOLDER'], exist_ok=True)
os.makedirs(app.config['PATIENT_DICOM_FOLDER'], exist_ok=True)


# Utility function for checking allowed file extensions
def allowed_file(filename, allowed_extensions):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
