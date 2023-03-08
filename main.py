from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.utils import secure_filename

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

# Create the database model
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/database'
app.secret_key = 'your_secret_key_here'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class FileUploads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)

@app.route('/')
@login_required
def home():
    uploads = FileUploads.query.all()
    uploads = sorted(uploads, key=lambda x: x.time, reverse=True)
    return render_template('index.html', uploads=uploads)

class LoginForm(FlaskForm):
    username = StringField(label='Username', validators=[InputRequired(), Length(min=1, max=50)])
    password = PasswordField(label='Password', validators=[InputRequired(), Length(min=1, max=60)])
    submit = SubmitField(label='Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
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

@app.route('/process', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')

        if files[0].filename == '':
            flash('No selected file')

        else:
            for file in files:
                file_name = secure_filename(file.filename)
                time = str(datetime.datetime.now().replace(microsecond=0))
                #formatted_time = time.strftime("%d-%m-%Y @ %I:%M %p")
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
