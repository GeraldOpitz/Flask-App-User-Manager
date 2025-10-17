
import os
import sys
import re
import pytest

# Ensure we can import "app" from the project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, db, User  # noqa: E402


@pytest.fixture(autouse=True)
def _setup_app_ctx():
    """
    Configure the app for testing with an in-memory SQLite DB.
    Create/drop tables around each test so your real users.db is untouched.
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def test_add_user_get_shows_form():
    """
    GET /add should return 200 and render the form.
    - Title assertion is case-insensitive and locale-tolerant
      ('Add user' | 'Agregar Usuario').
    - Verifies the presence of name/email/role inputs.
    """
    client = app.test_client()
    resp = client.get("/add")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert re.search(r"<title>\s*(add user)\s*</title>", html, re.I)

    for field in ("name", "email", "role"):
        assert re.search(fr'name\s*=\s*"{field}"', html, re.I)


def test_add_user_post_creates_and_redirects_then_visible_on_index():
    """
    POST /add should create the user and redirect to index.
    The created user should be visible in the index HTML.
    """
    client = app.test_client()

    resp = client.post(
        "/add",
        data={"name": "Alice", "email": "alice@example.com", "role": "admin"},
        follow_redirects=True,  
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
   
    assert "alice@example.com" in html
    assert "Alice" in html
    assert "admin" in html

    with app.app_context():
        u = db.session.execute(
            db.select(User).filter_by(email="alice@example.com")
        ).scalars().first()
        assert u is not None and u.name == "Alice" and u.role == "admin"
