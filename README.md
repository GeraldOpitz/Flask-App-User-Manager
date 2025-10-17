# User Manager (Flask)

A web application built with Flask that allows you to manage users through CRUD operations (Create, Read, Update, Delete).  
Each user has a **name**, **email**, and **role**.  
This project demonstrates how to use **Flask**, **SQLAlchemy**, and **SQLite** to build a small web app with a database and templates.

---

## Features

- Create, view, edit, and delete users  
- Store data in a local SQLite database  
- Built with Flask and SQLAlchemy  
- Simple HTML interface  
- Easy to extend and modify  

---

## Technologies Used

- Python
- Flask
- SQLAlchemy  
- SQLite  
- Jinja2
- Pytest
- Docker
- Bash
- HTML
- CSS

---

## Project Structure

```bash
Flask-App-User-Manager/
├─ app.py
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
├─ setup.sh
├─ templates/          
├─ static/              # CSS/JS/assets
└─ tests/               # pytest (unit & integration)
```



## Installation and Setup

1. **Clone the repository**:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

2. Run the setup script:
./setup.sh
if you are using WSL you may need to run:

```bash
sudo apt update && sudo apt install dos2unix -y 
dos2unix setup.sh
```

4. Open the container in Docker Desktop and visit http://127.0.0.1:5000
 in your browser.

