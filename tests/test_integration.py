
import os
import sys
import re
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, db, User  # noqa: E402


@pytest.fixture(autouse=True)
def _setup_app_ctx():
    """
    Configure the app for integration tests:
    - TESTING mode
    - In-memory SQLite DB
    - Create/drop tables around each test
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def _html(client, path="/"):
    """GET a path and return (status_code, text_html)."""
    resp = client.get(path)
    assert resp.headers["Content-Type"].startswith("text/html")
    return resp.status_code, resp.get_data(as_text=True)


def _create_user(name="Alice", email="alice@example.com", role="admin"):
    with app.app_context():
        u = User(name=name, email=email, role=role)
        db.session.add(u)
        db.session.commit()
        return u.id


# ---------------------- Basic availability & index ---------------------- #

def test_index_empty_state_and_content_type():
    client = app.test_client()
    code, html = _html(client, "/")
    assert code == 200
    # Accept English or Spanish title
    assert ("<title>Users</title>" in html) or ("<title>Usuarios</title>" in html)
    # No known users yet
    assert "alice@example.com" not in html
    assert "bob@example.com" not in html


# ---------------------- Add (GET + POST) ---------------------- #

def test_add_get_renders_form():
    client = app.test_client()
    code, html = _html(client, "/add")
    assert code == 200

    # Case-insensitive, locale-tolerant title check:
    # accepts "<title>Add user</title>" or "<title>Agregar usuario</title>" in any casing
    html_lower = html.lower()
    assert (
        "<title>add user</title>" in html_lower
        or "<title>agregar usuario</title>" in html_lower
    ), f"Unexpected /add page title. Got: {html}"

    # Basic form fields should be present (case-insensitive, whitespace-tolerant)
    for field in ("name", "email", "role"):
        assert re.search(fr'name\s*=\s*"{field}"', html, re.I), f'Missing input "{field}" in form'


def test_add_post_creates_user_and_redirects_then_visible_on_index():
    client = app.test_client()

    # POST /add (do not follow redirect to assert 30x)
    resp = client.post(
        "/add",
        data={"name": "Alice", "email": "alice@example.com", "role": "admin"},
    )
    assert resp.status_code in (301, 302)

    # Now the user should appear on the index
    code, html = _html(client, "/")
    assert code == 200
    assert "Alice" in html and "alice@example.com" in html and "admin" in html

    # DB cross-check
    with app.app_context():
        u = db.session.execute(
            db.select(User).filter_by(email="alice@example.com")
        ).scalars().first()
        assert u is not None and u.name == "Alice" and u.role == "admin"


# ---------------------- Edit (GET + POST) ---------------------- #

def test_edit_get_prefilled_form_for_existing_user():
    user_id = _create_user()
    client = app.test_client()

    code, html = _html(client, f"/edit/{user_id}")
    assert code == 200
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


# ---------------------- Delete ---------------------- #

def test_delete_user_removes_and_redirects_then_absent_on_index():
    user_id = _create_user(name="Bob", email="bob@example.com", role="user")
    client = app.test_client()

    # Perform deletion and follow redirect back to index
    resp = client.get(f"/delete/{user_id}", follow_redirects=True)
    assert resp.status_code == 200

    html = resp.get_data(as_text=True)

    # Accept English or Spanish title; don't rely on a specific empty-state string
    assert ("<title>Users</title>" in html) or ("<title>Usuarios</title>" in html)
    # The deleted user's email should not appear anymore
    assert "bob@example.com" not in html
    # Optional: ensure there are no user rows left (if your index renders a table)
    assert not re.search(r"<tr>.*@.*</tr>", html, flags=re.I | re.S)


# ---------------------- Not found (404) ---------------------- #

def test_edit_404_when_user_not_found():
    client = app.test_client()
    resp = client.get("/edit/999999")
    assert resp.status_code == 404


def test_delete_404_when_user_not_found():
    client = app.test_client()
    resp = client.get("/delete/999999")
    assert resp.status_code == 404


# ---------------------- Multi-step end-to-end ---------------------- #

def test_full_http_flow_add_edit_delete():
    """
    Full E2E across the HTTP layer:
    - GET index (empty)
    - POST /add (Alice)
    - POST /add (Bob)
    - GET /edit/<alice_id> (prefilled)
    - POST /edit/<alice_id> (update)
    - GET /delete/<bob_id> (remove)
    - GET index (final state)
    """
    client = app.test_client()

    # Empty start
    code, html = _html(client, "/")
    assert code == 200
    assert ("<title>Users</title>" in html) or ("<title>Usuarios</title>" in html)
    assert "alice@example.com" not in html and "bob@example.com" not in html

    # Add Alice
    r = client.post("/add", data={"name": "Alice", "email": "alice@example.com", "role": "admin"})
    assert r.status_code in (301, 302)

    # Add Bob
    r = client.post("/add", data={"name": "Bob", "email": "bob@example.com", "role": "user"})
    assert r.status_code in (301, 302)

    # Confirm both visible
    _, html = _html(client, "/")
    assert "Alice" in html and "alice@example.com" in html and "admin" in html
    assert "Bob" in html and "bob@example.com" in html and "user" in html

    # Find IDs (via DB)
    with app.app_context():
        ids = {u.email: u.id for u in User.query.all()}
        alice_id, bob_id = ids["alice@example.com"], ids["bob@example.com"]

    # Edit GET (prefilled)
    code, form_html = _html(client, f"/edit/{alice_id}")
    assert code == 200
    assert 'value="Alice"' in form_html
    assert 'value="alice@example.com"' in form_html
    assert 'value="admin"' in form_html

    # Edit POST (update)
    r = client.post(
        f"/edit/{alice_id}",
        data={"name": "Alice Updated", "email": "alice2@example.com", "role": "owner"},
    )
    assert r.status_code in (301, 302)

    # Delete Bob
    r = client.get(f"/delete/{bob_id}")
    assert r.status_code in (301, 302)

    # Final index reflects updates
    _, html = _html(client, "/")
    # Use a tolerant pattern for the updated row
    row_pattern = re.compile(
        r"<tr[^>]*>.*?"
        r"<td[^>]*>.*?Alice\s*Updated.*?</td>.*?"
        r"<td[^>]*>.*?alice2@example\.com.*?</td>.*?"
        r"<td[^>]*>.*?owner.*?</td>.*?"
        r"</tr>",
        flags=re.I | re.S,
    )
    assert row_pattern.search(html)
    assert "bob@example.com" not in html

    # DB final state
    with app.app_context():
        a = db.session.execute(db.select(User).filter_by(email="alice2@example.com")).scalars().first()
        assert a is not None and a.name == "Alice Updated" and a.role == "owner"
        b = db.session.execute(db.select(User).filter_by(email="bob@example.com")).scalars().first()
        assert b is None
