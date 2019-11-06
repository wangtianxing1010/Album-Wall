import unittest

from flask import url_for

from app import create_app
from app.extensions import db
from app.models import User, Photo, Role, Tag, Comment


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        app = create_app('testing')
        self.context = app.test_request_context()
        self.context.push()
        self.client = app.test_client()
        self.runner = app.test_cli_runner()

        db.create_all()
        Role.init_role()

        admin_user = User(email="admin@test.com", name="Admin User", username='admin', confirmed=True)
        admin_user.set_password('123456')
        admin_user.set_role(2)
        common_user = User(email="common@test.com", name="Common User", username='common', confirmed=True)
        common_user.set_password('123456')
        unconfirmed_user = User(email="unconfirmed@test.com", name="Unconfirmed", username='unconfirmed', confirmed=False)
        unconfirmed_user.set_password('123456')
        locked_user = User(email="locked@test.com", name="Locked User", username='locked', confirmed=True,
                           locked=True)
        locked_user.set_password('123456')
        locked_user.lock()
        blocked_user = User(email="blocked@test.com", name="Blocked User", username='blocked', confirmed=True,
                            active=False)
        blocked_user.set_password('123456')

        photo = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                      description='Photo 1', author=admin_user)
        photo2 = Photo(filename='test2.jpg', filename_s='test2_s.jpg', filename_m='test2_m.jpg',
                      description='Photo 2', author=common_user)

        comment = Comment(body='test comment body', photo=photo, author=common_user)
        tag = Tag(name='test tag')
        photo.tags.append(tag)
        # db.session.add_all([photo, photo2, comment, tag])
        db.session.add_all([admin_user, common_user, unconfirmed_user, locked_user, blocked_user])
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.context.pop()

    def login(self, email=None, password=None):
        if email is None and password is None:
            email = "common@test.com"
            password = '123456'

        return self.client.post(url_for('auth.login'), data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get(url_for('auth.logout'), follow_redirects=True)






