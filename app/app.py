import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import DataError, IntegrityError

load_dotenv()

load_dotenv()

app = Flask(__name__)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

# Add a new user
@app.route('/add', methods=['GET', 'POST'])
def add_user():
    error_message = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']

        new_user = User(name=name, email=email, role=role)
        db.session.add(new_user)
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except DataError as _:
            db.session.rollback()
            error_message = "Error: Some data is too long for the database fields."
        except IntegrityError as _:
            db.session.rollback()
            error_message = "Error: A user with that email already exists."
        except Exception as _:
            db.session.rollback()
            error_message = "Error: Something went wrong. Please try again."

    return render_template('add_user.html', error_message=error_message)

# Edit a user
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    error_message = None
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.role = request.form['role']
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except DataError as _:
            db.session.rollback()
            error_message = "Error: Some data is too long for the database fields."
        except IntegrityError as _:
            db.session.rollback()
            error_message = "Error: A user with that email already exists."
        except Exception as _:
            db.session.rollback()
            error_message = "Error: Something went wrong. Please try again."

    return render_template('edit_user.html', user=user, error_message=error_message)

# Delete a user
@app.route('/delete/<int:id>')
def delete_user(id):
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as _:
        db.session.rollback()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database and tables created successfully.")
        app.run(host='0.0.0.0', port=5000, debug=True)
