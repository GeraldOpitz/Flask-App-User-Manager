
import os
import sys
import re
import pytest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.app import app, db, User  # noqa: E402

#
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

# Helpers
def _create_user(name="Alice", email="alice@example.com", role="admin"):
    with app.app_context():
        u = User(name=name, email=email, role=role)
        db.session.add(u)
        db.session.commit()
        return u.id


def test_edit_user_get_prefilled_form():
    """
    GET /edit/<id> should render the form prefilled with existing user data.
    """
    user_id = _create_user()
    client = app.test_client()

    resp = client.get(f"/edit/{user_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Accept English or Spanish title
    assert ("<title>Edit User</title>" in html) or ("<title>Editar Usuario</title>" in html)
    assert 'value="Alice"' in html
    assert 'value="alice@example.com"' in html
    assert 'value="admin"' in html


def test_edit_user_post_updates_and_redirects():
    """
    POST /edit/<id> should update the user and redirect to index.
    The index HTML should contain a single <tr> where the three <td> cells
    (in order) contain: Alice Updated, alice2@example.com, owner.
    This regex is tolerant to inner tags (e.g., <a>, <span>) and whitespace.
    """
    user_id = _create_user()
    client = app.test_client()

    resp = client.post(
        f"/edit/{user_id}",
        data={"name": "Alice Updated", "email": "alice2@example.com", "role": "owner"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Robust row pattern: same <tr>, cells in order, any markup/whitespace allowed
    row_pattern = re.compile(
        r"<tr[^>]*>.*?"                                  # start of row
        r"<td[^>]*>.*?Alice\s*Updated.*?</td>.*?"        # name cell (allows inner tags)
        r"<td[^>]*>.*?alice2@example\.com.*?</td>.*?"    # email cell
        r"<td[^>]*>.*?owner.*?</td>.*?"                  # role cell
        r"</tr>",                                        # end of row
        flags=re.I | re.S,
    )

    assert row_pattern.search(html), (
        "Updated row not found in HTML after edit. Expected a single <tr> "
        "containing, in order: 'Alice Updated', 'alice2@example.com', 'owner'."
    )

    # DB sanity check
    with app.app_context():
        updated = db.session.execute(
            db.select(User).filter_by(email="alice2@example.com")
        ).scalars().first()
        assert updated is not None and updated.name == "Alice Updated" and updated.role == "owner"


def test_edit_user_404_when_not_found():
    client = app.test_client()
    resp = client.get("/edit/999999")
    assert resp.status_code == 404
