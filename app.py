from flask import Flask
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from ehr_system.config import Config
from ehr_system.models import db, UserDoctor
from ehr_system.routes import register_routes
from flask_login import LoginManager

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

# Initialize extensions
mail = Mail(app)
app.ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to 'login' route for unauthorized access


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return UserDoctor.query.get(int(user_id))


# Initialize SQLAlchemy
db.init_app(app)

# Create tables (if they don't already exist)
with app.app_context():
    db.create_all()

# Register routes
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
