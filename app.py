"""
On-Premises HR Management System
Main application entry point
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os

# Initialize Flask app
app = Flask(__name__)

# Use environment variable for SECRET_KEY for security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

# --- Database Configuration ---
# Use PostgreSQL if DATABASE_URL is set, otherwise use SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/hrm.db'
# --- End Database Configuration ---

# Import db from database.py
from database import db
from flask_migrate import Migrate

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import models
from models import (
    User, Employee, Department, Position, Attendance, Leave, Payroll
)

# Import and register blueprint
from routes import bp
app.register_blueprint(bp)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
