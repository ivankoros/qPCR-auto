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

    def test_login_successful(self):
        response = self.app.post('/login',
                                 data=dict(username='testuser', password='testpassword'),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testfile.txt', response.data)

    def test_login_failed(self):
        response = self.app.post('/login',
                                 data=dict(username='wronguser', password='wrongpassword'),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username', response.data)

    def test_register_successful(self):
        with patch.dict(os.environ, {'REGISTRATION_KEY': 'testkey'}):
            response = self.app.post('/register',
                                     data=dict(username='newuser',
                                               password='newpassword',
                                               registration_key='testkey'),
                                     follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User created successfully', response.data)

    def test_register_failed(self):
        with patch.dict(os.environ, {'REGISTRATION_KEY': 'testkey'}):
            response = self.app.post('/register',
                                     data=dict(username='newuser',
                                               password='newpassword',
                                               registration_key='wrongkey'),
                                     follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid registration key', response.data)

    def test_login_required(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_upload_file(self):
        self.app.post('/login',
                      data=dict(username='testuser', password='testpassword'),
                      follow_redirects=True)

        with open('tests/testfiles/raw_counts.xlsx', 'rb') as raw_counts:
            with open('tests/testfiles/plate_diagram.xlsx', 'rb') as plate_diagram:
                response = self.app.post('/process',
                                         data=dict(raw_counts=raw_counts, plate_diagram=plate_diagram),
                                         follow_redirects=True,
                                         content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)



if __name__ == '__main__':
    unittest.main()

