import os
from app import app, db
from models import User

with app.app_context():
    # Get admin credentials from environment variables
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')

    # Check if admin user exists
    admin_user = User.query.filter_by(username=admin_username).first()
    if not admin_user:
        # Create admin user
        admin = User(username=admin_username, role='admin')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user '{admin_username}' created successfully!")
    else:
        print(f"Admin user '{admin_username}' already exists.")
