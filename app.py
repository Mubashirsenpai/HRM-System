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

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Import models and routes
# Ensure models.py and routes.py are in the same directory or correctly imported
from models import (
    User, Employee, Department, Position, Attendance, Leave, Payroll
)
from routes import (
    dashboard, employees, add_employee, edit_employee,
    delete_employee, departments, add_department, view_department,
    edit_department, delete_department, positions, add_position,
    edit_position, delete_position, leave, add_leave,
    edit_leave, delete_leave, view_leave,
    attendance, add_attendance, edit_attendance,
    delete_attendance, payroll, generate_payroll,
    login, logout, bulk_upload_employees, sample_csv, sample_excel
)

# Create all database tables based on models.py
# This will create tables in your PostgreSQL database
with app.app_context():
    db.create_all()
    print("Database tables created in PostgreSQL.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

