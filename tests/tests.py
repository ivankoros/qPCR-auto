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
        """Test that a user can log in successfully (correct password and username)

        This test is done to ensure that the login functionality works as expected
         and allows users with valid credentials to access the application.

        """
        response = self.app.post('/login',
                                 data=dict(username='testuser', password='testpassword'),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testfile.txt', response.data)

    def test_login_failed(self):
        """Test if a user can fail to log in (wrong password and username).

        This test checks that the application denies access to users with
        incorrect credentials and provides an appropriate error message,
        maintaining the security of the application.

        """
        response = self.app.post('/login',
                                 data=dict(username='wronguser', password='wrongpassword'),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username', response.data)

    def test_register_successful(self):
        """Test if a user can successfully register (valid registration key).

        This test ensures that the registration process is functional and
        allows new users to register when provided with a correct registration key.

        """
        with patch.dict(os.environ, {'REGISTRATION_KEY': 'testkey'}):
            response = self.app.post('/register',
                                     data=dict(username='newuser',
                                               password='newpassword',
                                               registration_key='testkey'),
                                     follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User created successfully', response.data)

    def test_register_failed(self):
        """Test if a user can fail to register (invalid registration key).

        This test is done to verify that the application denies
        registration to users with incorrect registration keys, thereby
        ensuring that only authorized users can register.

        """
        with patch.dict(os.environ, {'REGISTRATION_KEY': 'testkey'}):
            response = self.app.post('/register',
                                     data=dict(username='newuser',
                                               password='newpassword',
                                               registration_key='wrongkey'),
                                     follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid registration key', response.data)

    def test_login_required(self):
        """Test if the login_required decorator works as expected

        This test confirms that the login_required decorator is effectively
        protecting routes that require authentication, thereby maintaining access
        control for specific parts of the application.

        """
        response = self.app.get('/', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_upload_file(self):
        """Test if the file upload route works correctly (we can go to it).

        This test ensures that the file upload process is working
        properly, enabling users to upload valid files, store them
        in the database, and display the uploaded files on the home page.

        """
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

    def test_validate_file_valid(self):
        """Test if the file validation route returns valid when given a file with the expected dimensions and/or content.

        This test verifies that the file validation route can correctly identify valid files based on their
         dimensions, allowing for accurate processing of valid files in the application.
        :return:
        """
        with open('tests/testfiles/raw_counts.xlsx', 'rb') as file:
            response = self.app.post('/validate_file/96x16',
                                     data=dict(file=file),
                                     content_type='multipart/form-data')

        self.assertIn(b'true', response.data)

    def test_validate_file_invalid(self):
        """Test if the file validation route returns invalid when given a file with incorrect dimensions and/or content.

        This test ensures that the file validation route can identify invalid files based on their dimensions
        and prevent them from being processed by the application, maintaining data integrity and avoiding potential
        errors.

        """
        with open('tests/testfiles/invalid_dimensions.xlsx' 'rb') as file:
            response = self.app.post('/validate_file/96x16',
                                     data=dict(file=file),
                                     content_type='multipart/form-data')

        self.assertIn(b'false', response.data)


if __name__ == '__main__':
    unittest.main()

