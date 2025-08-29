"""
On-Premises HR Management System
Main application entry point
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os

# Initialize Flask app
app = Flask(__name__)

# Use environment variable for SECRET_KEY for security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application. Set the SECRET_KEY environment variable.")

# --- PostgreSQL Database Configuration ---
# Replace with your PostgreSQL credentials and database name
# Example: 'postgresql://username:password@localhost:5432/hrm_db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# --- End PostgreSQL Configuration ---

# Import db from database.py
from database import db
from flask_migrate import Migrate

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

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
