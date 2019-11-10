from flask import url_for

from tests.base import BaseTestCase
from app.extensions import db
from app.models import User


class AuthTestCase(BaseTestCase):

    def setUp(self):
        super(AuthTestCase, self).setUp() # what is setUp() for ??
        self.login() # login as common user

    def test_login(self):
        # test already logged in
        response = self.client.get(url_for('auth.login'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Logged in as common', data)
        # test common user correct email, password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='common@test.com', password='123456'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success', data)
        self.assertIn('Logged in as common', data)
        # User doesn't exit
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='doesnotexist@test.com', password='123456'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # User is blocked
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='blocked@test.com', password='123456'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Your account is blocked', data)

        # WRONG
        # test common user correct email, wrong password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='common@test.com', password='wrong'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # test common user wrong email, correct password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='wrong@test.com', password='123456'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # test common user wrong email, wrong password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='wrong@test.com', password='wrong'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        ## EMPTY
        # test common user correct email, empty password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            email='common@test.com'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # test common user empty email, correct password
        self.logout()
        response = self.client.post(url_for('auth.login', data=dict(
            password='123456'
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # test common user empty email, empty password
        self.logout()
        response = self.client.post(url_for('auth.login'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password', data)

        # EMPTY + WRONG ??

    def test_re_authenticate(self):
        # already logged in
        response = self.client.get(url_for('auth.re_authenticate'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Logged in as common", data)

        # logged in required
        self.logout()
        response = self.client.get(url_for('auth.re_authenticate'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Please log in to access this page", data)

    def test_logout(self):
        # already logged in
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Logout success', data)

        # logged in required
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout success', data)
        self.assertIn('Please log in to access this page', data)

    def test_register(self):
        # already logged in
        response = self.client.get(url_for('auth.register'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Logged in as common', data)

        # not logged in
        self.logout()
        response = self.client.get(url_for('auth.register'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Already have an account?', data)
        # successfully registered an account
        response = self.client.post(url_for('auth.register', data=dict(
            name = 'New Name',
            email = 'new@test.com',
            username = 'new',
            password = '123456',
        )), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Confirm email sent, check your inbox", data)
        # test new user exists
        user = User.query.filter_by(email='new@test.com').first()
        self.assertEqual(user.username, "new")
        self.assertEqual(user.email, "new@test.com")

    def test_confirm(self):
        # already logged in user already confirmed
        res = self.client.get(url_for('auth.confirm'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn("Please logged in to access", data)
        self.assertIn('Logged in as common', data)

        # login required
        self.logout()
        res = self.client.get(url_for('auth.confirm'), follow_redirects=True)
        data = res.get_data(as_text=True)
        user = User.query.get(2)
        self.assertIn("Please log in to access", data)
        self.assertNotIn('Logged in as', data)
        self.assertEqual(user.confirmed, True)

        # logged in but not confirmed
        self.login(email='unconfirmed@test.com', password='123456')
        user = User.query.get(3)
        # ??
        token = 'correct token'
        # empty token
        res = self.client.post(url_for('auth.confirm'), data=dict())
        data = res.get_data(as_text=True)
        self.assertIn("Invalid or expired token", data)
        self.assertIn("Logged in as unconfirmed")
        self.assertNotIn("Account confirmed")
        self.assertEqual(user.confirmed, False)
        # wrong token
        res = self.client.post(url_for('auth.confirm'), data=dict(
            token="wrongtoken",
            operation = "confirm"
        ))
        data = res.get_data(as_text=True)
        self.assertIn("Invalid or expired token", data)
        self.assertIn("Logged in as unconfirmed")
        self.assertNotIn("Account confirmed")
        self.assertEqual(user.confirmed, False)
        # correct token
        res = self.client.post(url_for('auth.confirm'), data=dict(
            token=token,
            operation="confirm"
        ))
        data = res.get_data(as_text=True)
        self.assertNotIn("Invalid or expired token", data)
        self.assertIn("Account confirmed")
        self.assertIn("Logged in as unconfirmed")
        self.assertEqual(user.confirmed, True)

    def test_resend_confirm_email(self):
        # logged in & user already confirmed
        res = self.client.get(url_for('auth.resend_confirm_email'), follow_redirects=True)
        data = res.get_data(as_text=True)
        user = User.query.get(2)
        self.assertNotIn("Please logged in to access", data)
        self.assertIn('Logged in as', data)
        self.assertEqual(user.confirmed, True)

        # logged in required
        self.logout()
        res = self.client.get(url_for('auth.resend_confirm_email'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Please logged in to access", data)
        self.assertNotIn('Logged in as', data)

        # logged in but not confirmed
        self.login(email='unconfirmed@test.com', password='123456')
        user = User.query.get(3)

        res = self.client.get(url_for('auth.resend_confirm_email'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn("Please logged in to access", data)
        self.assertIn("New email sent, check your inbox", 'info', data)
        self.assertIn("Logged in as unconfirmed", data)
        self.assertEqual(user.confirmed, False)

    def test_forget_password(self):
        # already logged in
        res = self.client.get(url_for('auth.forget_password'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Logged in as common')
        self.assertNotIn("Please login to access", data)
        self.assertNotIn("<h1>Password Reset</h1>", data)

        self.logout()
        # Wrong email
        res = self.client.post(url_for('auth.forget_password', data=dict(
            email='wrongemail@test.com'
        )), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn('Password reset email to you, check your inbox', data)
        self.assertIn('Invalid email', data)
        self.assertIn("<h1>Password Reset</h1>", data)

    def test_reset_password(self):
        # already logged in
        res = self.client.get(url_for('auth.reset_password'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Logged in as common')
        self.assertNotIn("Please login to access", data)
        self.assertNotIn("<h1>Password Reset</h1>", data)

        self.logout()
        # user doesn't exist
        res = self.client.post(url_for('auth.reset_password', data=dict(
            email='doesnotexist@test.com'
        )), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn('Logged in as common')
        self.assertNotIn("Please login to access", data)
        self.assertIn("<h1>Password Reset</h1>", data)
        # invalid token
        res = self.client.post(url_for('auth.reset_password', data=dict(
            email='common@test.com',
            token='invalidtoken'
        )), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn('Logged in as common')
        self.assertNotIn("Please login to access", data)
        self.assertIn("<h1>Password Reset</h1>", data)
        # correct token
        res = self.client.post(url_for('auth.reset_password', data=dict(
            email='common@test.com',
            token='correcttoken'
        )), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertNotIn('Logged in as common')
        self.assertNotIn("Please login to access", data)
        self.assertNotIn("<h1>Password Reset</h1>", data)
        self.assertIn("Password updated", data)
        self.assertIn("Logged in as common")


