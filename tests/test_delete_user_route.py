# tests/test_delete_user_route.py
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from jinja2 import DictLoader
from app import app, db, User

#
@pytest.fixture(autouse=True)
def _setup_app_ctx():
    """Configure in-memory DB and in-memory templates per test."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Minimal templates so we don't depend on real /templates files
    app.jinja_loader = DictLoader({
        "index.html": """<!doctype html>
<title>Users</title>
<ul>
{% for u in users %}
  <li>{{ u.name }} - {{ u.email }} ({{ u.role }})</li>
{% else %}
  <li>No users</li>
{% endfor %}
</ul>"""
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

# Tests for DELETE /delete
def test_delete_user_removes_and_redirects():
    """GET /delete/<id> should delete the user and redirect to index."""
    user_id = _create_user()
    client = app.test_client()

    resp = client.get(f"/delete/{user_id}", follow_redirects=True)
    assert resp.status_code == 200

    html = resp.get_data(as_text=True)

    assert "No users" in html


    with app.app_context():
        assert db.session.get(User, user_id) is None

# Tests for 404 errors
def test_delete_user_404_when_not_found():
    """GET /delete/<id> with a non-existent id should return 404."""
    client = app.test_client()
    resp = client.get("/delete/9999")
    assert resp.status_code == 404
