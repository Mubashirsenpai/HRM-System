"""
On-Premises HR Management System
Main application entry point
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '6b1422bcece6041cf99a2d8b68b28f6f275f684ddc7ed1e4'

# --- PostgreSQL Database Configuration ---
# Replace with your PostgreSQL credentials and database name
# Example: 'postgresql://username:password@localhost:5432/hrm_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_0uNK5hdxmSeF@ep-curly-cherry-ab5ccqs5-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
# --- End PostgreSQL Configuration ---

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models and routes
# Ensure models.py and routes.py are in the same directory or correctly imported
from models import *
from routes import *

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables based on models.py
        # This will create tables in your PostgreSQL database
        db.create_all()
        print("Database tables created/checked in PostgreSQL.")
    app.run(debug=True, host='0.0.0.0', port=5000)

