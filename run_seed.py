from app import app, db
from seed_admin import create_admin_user

with app.app_context():
    create_admin_user()
    print("Admin user created successfully!")
