# tests/test_edit_user_route.py
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from jinja2 import DictLoader
from app import app, db, User

# Fixture to set up app context and in-memory DB
@pytest.fixture(autouse=True)
def _setup_app_ctx():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    app.jinja_loader = DictLoader({
        "index.html": """<!doctype html>
<title>Users</title>
<ul>
{% for u in users %}
  <li>{{ u.name }} - {{ u.email }} ({{ u.role }})</li>
{% else %}
  <li>No users</li>
{% endfor %}
</ul>""",
        "edit_user.html": """<!doctype html>
<title>Edit User</title>
<form method="post">
  <input type="text"   name="name"  value="{{ user.name }}">
  <input type="email"  name="email" value="{{ user.email }}">
  <input type="text"   name="role"  value="{{ user.role }}">
  <button type="submit">Save</button>
</form>"""
    })

    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

# Helper to create a user
def _create_user(name="Alice", email="alice@example.com", role="admin"):
    with app.app_context():
        u = User(name=name, email=email, role=role)
        db.session.add(u)
        db.session.commit()
        return u.id

# Tests for GET /edit
def test_edit_user_get_prefills_form():
    user_id = _create_user()
    client = app.test_client()

    resp = client.get(f"/edit/{user_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "<title>Edit User</title>" in html
    assert 'value="Alice"' in html
    assert 'value="alice@example.com"' in html
    assert 'value="admin"' in html

# Tests for POST /edit
def test_edit_user_post_updates_and_redirects():
    user_id = _create_user()
    client = app.test_client()

    resp = client.post(
        f"/edit/{user_id}",
        data={"name": "Alice Updated", "email": "alice2@example.com", "role": "owner"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Alice Updated - alice2@example.com (owner)" in html

    with app.app_context():
        got = db.session.get(User, user_id)
        assert got is not None
        assert got.name == "Alice Updated"
        assert got.email == "alice2@example.com"
        assert got.role == "owner"

# Tests for 404 errors
def test_edit_user_404_when_not_found():
    client = app.test_client()
    resp = client.get("/edit/9999")
    assert resp.status_code == 404
