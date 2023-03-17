# Imports
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

# Load dotenv environment variables
load_dotenv(override=True)

# Create the database model
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = os.getenv('APP_DB_SECRET_KEY')  # Secret key for session management


# Create the database model
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


# Class for the database model for the users and login manager implementation
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Class for the database for uploads
class FileUploads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)

# Home page that displays the uploads if the user is logged in
@app.route('/')
@login_required
def home():
    uploads = FileUploads.query.all()
    uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
    return render_template('index.html', uploads=uploads)

# Login page input form and validation using Flask-WTF
class LoginForm(FlaskForm):
    username = StringField(label='Username', validators=[InputRequired(), Length(min=1, max=50)])
    password = PasswordField(label='Password', validators=[InputRequired(), Length(min=1, max=60)])
    submit = SubmitField(label='Login')

# Login page that displays the login form and validates the user if they are in the database
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route and validation

    Checks if the user is in the database and if they are, logs them in.
    If the user is not in the database, they are redirected to the login page.

    Once the user is validated and redirected, the file table is queried and rendered.

    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid username')
        else:
            login_user(user)
            uploads = FileUploads.query.all()
            uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
            return render_template('index.html', uploads=uploads)

    return render_template('login.html')

# Process route that handles the file uploads and adds them to the database with the file name and current time
@app.route('/process', methods=['GET', 'POST'])
def upload_file():
    """File upload process route

    When a file is uploaded, the file name and current time is added to the database.
    The database is then queried and the table is updated with the new entry with javascript.

    """
    if request.method == 'POST':
        files = request.files.getlist('file')

        if files[0].filename == '':
            flash('No selected file')

        else:
            for file in files:
                file_name = secure_filename(file.filename)
                time = str(datetime.datetime.now().replace(microsecond=0))
                new_entry = FileUploads(name=file_name,
                                        time=str(time))
                db.session.add(new_entry)
                db.session.commit()
                print("File uploaded: " + file_name)

            uploads = FileUploads.query.all()
            uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
            update_table = render_template('update_table.html', uploads=uploads)

            return jsonify({'update_table': update_table})

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
