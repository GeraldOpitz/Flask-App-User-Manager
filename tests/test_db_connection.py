import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from sqlalchemy import text, inspect
from app.app import app, db, User

# Configure the app for testing
@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """
    Configure the app to use a temporary on-disk SQLite DB.
    Create tables before each test and drop them afterwards.
    """
    app.config["TESTING"] = True
    db_path = tmp_path / "users_test.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

# Test cases for DB connection and User model
def test_db_can_connect_and_select_1():
    """The app should connect to the DB and run SELECT 1."""
    with app.app_context():
        result = db.session.execute(text("SELECT 1")).scalar_one()
        assert result == 1

# Test case for table creation
def test_tables_are_created():
    """Verify the User table exists in the DB."""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        # By default, SQLAlchemy uses the model name in lowercase: 'user'
        assert "user" in tables

# Test case for user insertion and querying
def test_insert_and_query_user():
    """Insert a User and verify it can be queried."""
    with app.app_context():
        u = User(name="Alice", email="alice@example.com", role="admin")
        db.session.add(u)
        db.session.commit()

        got = User.query.filter_by(email="alice@example.com").first()
        assert got is not None
        assert got.name == "Alice"
        assert got.role == "admin"
        