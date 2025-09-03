from app import app, db
from sqlalchemy import text

with app.app_context():
    # Delete the alembic_version row
    db.session.execute(text("DELETE FROM alembic_version"))
    db.session.commit()
    print("Alembic version table cleared")
