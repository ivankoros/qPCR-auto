import os
import unittest
from unittest.mock import patch
import datetime
from dotenv import load_dotenv
from main import app, db, User, FileUploads, LoginForm, RegisterForm

load_dotenv(override=True)

class FlaskAppTests(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.db'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = False

        self.app = app.test_client()

        db.create_all()

        self.test_user = User(username='testuser')
        self.test_user.set_password('testpassword')
        db.session.add(self.test_user)
        db.session.commit()

        self.test_upload = FileUploads(name='testfile.txt', time=datetime.datetime.now().replace(microsecond=0))
        db.session.add(self.test_upload)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


if __name__ == '__main__':
    unittest.main()

