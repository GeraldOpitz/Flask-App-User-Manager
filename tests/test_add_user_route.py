# tests/test_add_user_route.py
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from jinja2 import DictLoader
from app import app, db, User

# Setup a fresh app context for each test
@pytest.fixture(autouse=True)
def _setup_app_ctx():
    """
    Configure a fresh in-memory DB and in-memory templates for each test.
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Minimal templates so we don't depend on files in /templates
    app.jinja_loader = DictLoader({
        # Index shows users
        "index.html": """<!doctype html>
<title>Users</title>
<ul>
{% for u in users %}
  <li>{{ u.name }} - {{ u.email }} ({{ u.role }})</li>
{% else %}
  <li>No users</li>
{% endfor %}
</ul>""",
        # Add form template
        "add_user.html": """<!doctype html>
<title>Add User</title>
<form method="post">
  <input type="text"   name="name"  placeholder="Name">
  <input type="email"  name="email" placeholder="Email">
  <input type="text"   name="role"  placeholder="Role">
  <button type="submit">Save</button>
</form>"""
    })

    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

# Tests for /add route
def test_add_user_get_shows_form():
    """
    GET /add should return 200 and render the add form.
    """
    client = app.test_client()
    resp = client.get("/add")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "<title>Add User</title>" in html
    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'name="role"' in html

# Tests for /add route
def test_add_user_post_creates_and_redirects():
    """
    POST /add should create a user and redirect to index where the user is listed.
    """
    client = app.test_client()

    resp = client.post(
        "/add",
        data={"name": "Alice", "email": "alice@example.com", "role": "admin"},
        follow_redirects=True,  # follow to '/'
    )

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Alice - alice@example.com (admin)" in html

    with app.app_context():
        got = User.query.filter_by(email="alice@example.com").first()
        assert got is not None
        assert got.name == "Alice"
        assert got.role == "admin"
