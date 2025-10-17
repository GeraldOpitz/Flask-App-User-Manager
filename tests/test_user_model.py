import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from sqlalchemy.exc import IntegrityError
from app import app, db, User

# Configure the app for testing
@pytest.fixture(autouse=True)
def _setup_app_ctx():
    """Use an in-memory SQLite DB and create tables for each test."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

# Test cases user model
def test_create_user_and_query():
    u = User(name="Alice", email="alice@example.com", role="admin")
    db.session.add(u)
    db.session.commit()

    got = User.query.filter_by(email="alice@example.com").first()
    assert got is not None
    assert got.name == "Alice"
    assert got.role == "admin"

# Test for unique email constraint
def test_email_must_be_unique():
    
    db.session.add(User(name="Bob", email="bob@example.com", role="user"))
    db.session.commit()

    db.session.add(User(name="Bobby", email="bob@example.com", role="user"))
    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()
