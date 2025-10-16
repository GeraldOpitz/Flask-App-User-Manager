from flask import Flask

app = Flask(_name_)

@app.route('/')
def index():
    return "Flask app is running!"

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000, debug=True)