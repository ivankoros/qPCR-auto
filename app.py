from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
import json
import datetime
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import Length, Email, ValidationError

# Create the database model

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy()

db.init_app(app)

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.init_app(app)

# Import app routes by typing "from app import routes" in the python console
with app.app_context():
    db.create_all()


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        return password == self.password


class FileUploads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.id)


class LoginForm(Form):
    username = StringField(label='Username', validators=[Length(min=4, max=20)])
    password = PasswordField(label='Password', validators=[Length(min=6, max=60)])
    submit = SubmitField(label='Login')

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if not user:
            raise ValidationError('Username does not exist')

    def validate_password(self, password_to_check):
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            if not user.check_password(password_to_check.data):
                raise ValidationError('Incorrect password')


# Define the route for the default URL, which loads the form
@app.route('/')
def default():
    uploads = FileUploads.query.all()

    return render_template('index.html', uploads=uploads)


# Add uploaded file info to UploadFile sql table
@app.route('/process', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')

        for file in files:
            file_name = secure_filename(file.filename)
            new_entry = FileUploads(name=file_name, time=str(datetime.datetime.now().replace(microsecond=0, second=0)))
            db.session.add(new_entry)

            db.session.commit()

            print("File uploaded: " + file_name)

        uploads = FileUploads.query.all()
        update_table = render_template('update_table.html', uploads=uploads)

        return jsonify({'update_table': update_table})

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
