# Imports
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Regexp
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import html
import bcrypt
import pandas as pd

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
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

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

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
    uploads = FileUploads.query.all()  # Query the database for latest version
    uploads = sorted(uploads, key=lambda x: x.time, reverse=True)  # Sort the uploads by time
    return render_template('index.html', uploads=uploads)  # Render the home page with the uploads on the table

# Login page input form and validation using Flask-WTF

class LoginForm(FlaskForm):
    username = StringField(
        label='Username',
        validators=[
            InputRequired(),
            Length(min=1, max=50),
            Regexp('^[A-Za-z0-9_]+$',
                   message="Username must contain only letters, numbers, or underscores.")
        ])
    password = PasswordField(
        label='Password',
        validators=[
            InputRequired(),
            Length(min=1, max=50),
            Regexp('^[A-Za-z0-9_]+$',
                   message="Password must contain only letters, numbers, or underscores.")
        ])

    submit = SubmitField(label='Login')


class RegisterForm(FlaskForm):
    username = StringField(
        label='Username',
        validators=[
            InputRequired(),
            Length(min=1, max=50),
            Regexp(r'^[A-Za-z0-9_]+$',
                   message="Username must contain only letters (A-Z) and digits (0-9)."),
        ])
    password = PasswordField(
        label='Password',
        validators=[
            InputRequired(),
            Length(min=1, max=60),
            Regexp(r'^[A-Za-z0-9_]+$',
                   message="Password must contain only letters (A-Z) and digits (0-9)."),
        ])
    submit = SubmitField(label='Register')



# Login page that displays the login form and validates the user if they are in the database
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route and validation

    Checks if the user is in the database and if they are, logs them in.
    If the user is not in the database, they are redirected to the login page.

    Once the user is validated and redirected, the file table is queried and rendered.

    """
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid username')
        elif not user.check_password(password):
            flash('Invalid password')
        else:
            login_user(user)
            uploads = FileUploads.query.all()
            uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
            return render_template('index.html', uploads=uploads)

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        registration_key = os.getenv('REGISTRATION_KEY')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
        if registration_key != request.form['registration_key']:
            flash('Invalid registration key')
        else:
            new_user = User()
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)



# Process route that handles the file uploads and adds them to the database with the file name and current time
@app.route('/process', methods=['GET', 'POST'])
def upload_file():
    """File upload process route

    If the submit button is pressed and raw counts dropzone is valid and diagram dropzone is valid,
    take the two files and add them to the database with the file name and current time.

    Then update the table with the name of the raw counts file and date and time uploaded.

    """
    if request.method == 'POST':
        raw_counts_file = request.files['raw_counts']
        plate_diagram_file = request.files['plate_diagram']

        if raw_counts_file and plate_diagram_file:
            files = [raw_counts_file, plate_diagram_file]
            for file in files:
                file_name = secure_filename(file.filename)
                time = str(datetime.datetime.now().replace(microsecond=0))
                new_entry = FileUploads(name=file_name,
                                        time=str(time))
                db.session.add(new_entry)
                db.session.commit()
                print("File uploaded: " + file_name)

            # uploads = FileUploads.query.all()
            # uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
            # update_table = render_template('update_table.html', uploads=uploads)

            return jsonify({'status': 'success'})

    return render_template('index.html')


# TODO add check for excel or csv file
@app.route('/validate_file/<dimensions>', methods=['POST'])
def validate_file(dimensions):
    """Checks if uploaded file are valid by dimensions

    Depending on the dimensions of the file, the response data is different.
    If the file is the raw qpcr data then it is checked to be 96x16, and if it's
    the plate diagram file then it is checked to be 9x10.


    """
    file = request.files.get('file')
    df = pd.read_excel(file, engine='openpyxl')

    expected_dimensions = tuple(map(int, dimensions.split('x')))

    if df.shape == expected_dimensions:
        file_validation_response_data = {
            'dimensions_valid': True,
            'file_name': os.path.splitext(html.escape(file.filename))[0]  # Removing extension & escaping html
        }
    else:
        file_validation_response_data = {
            'dimensions_valid': False,
            'file_name': os.path.splitext(html.escape(file.filename))[0],  # Removing extension & escaping html
            'file_width': df.shape[1],
            'file_length': df.shape[0]
        }
    return jsonify(file_validation_response_data)


if __name__ == '__main__':
    app.run(debug=True)
