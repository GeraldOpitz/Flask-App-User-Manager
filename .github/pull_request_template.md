## Summary
Briefly describe what this Pull Request does within the User Manager app.

Example:  
> Implements the “reset password” endpoint and updates the Docker setup accordingly.

---

## Context
Explain why this change was needed — e.g., new feature, bugfix, or refactor — in the context of this CRUD Flask-SQLAlchemy application.

Example:  
> Users with “role=admin” could not be deleted, and the UI showed an error.

---

## Changes Made
List the key modifications introduced in this PR (code, tests, Docker, CI, etc.).

- [ ] Added new endpoint `/password/reset`
- [ ] Updated SQLAlchemy model `User` (added `last_login` field)
- [ ] Refactored `app.py` (moved user routes to `routes/users.py`)
- [ ] Fixed bug when deleting users with foreign key constraints
- [ ] Updated `Dockerfile` and `docker-compose.yml` for migration service
- [ ] Added Pytest tests for new functionality
- [ ] Updated README with setup instructions and badges

---

## Testing & Verification
Describe how the changes were tested — manual steps, automated tests, and CI integration.

Example:
1. Run `pytest` and confirm all tests pass (including new ones in `tests/test_user_password.py`).
2. Build Docker image (`docker build .`) and run `docker-compose up`, then visit http://localhost:5000/users.
3. Manual test: As admin, request password reset for `john.doe@example.com`, check mock email link, reset password, and log in.

---

## Screenshots (if applicable)
Include before/after UI changes, console output, or API response examples.

---

## Related Issues
Link any issue(s) this PR closes or references.

Example:  
Closes #12  
Related to #7  

---

## CI/CD & Deployment Notes
Describe any updates to GitHub Actions, Docker, or deployment configuration.

Example:  
> Added `ci-python.yml` workflow to run tests on Python 3.9 and 3.10.  
> Updated `docker-compose.yml` to include an Alembic migration service before app startup.

---

## Additional Notes
Provide any extra context, migration steps, or follow-up tasks.

Example:  
> The `last_login` field will be `NULL` for existing users; consider a data backfill script.  
> Follow-up: Add `/user/{id}/activity` endpoint in a future PR.

---

## Reviewers
@GeraldOpitz @MatiasValladares  
