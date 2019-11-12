from flask import url_for

from app.models import User, Photo
from tests.base import BaseTestCase


class UserTestCase(BaseTestCase):

    def test_index_page(self):
        response = self.client.get(url_for('user.index', username='common'))
        data = response.get_data(as_text=True)
        self.assertIn("Common User", data)

        self.login(email='locked@test.com', password='123456')
        response = self.client.get(url_for('user.index', username='locked'))
        data = response.get_data(as_text=True)
        self.assertIn("Your account is locked", data)
        self.assertIn("Locked User", data)

    def test_show_collections(self):
        response = self.client.get(url_for('user.show_collections', username='common'))
        data = response.get_data(as_text=True)
        self.assertIn("Common User's collection", data)
        self.assertIn("No collection", data)

        user = User.query.get(2)
        photo=Photo.query.get(1)
        collection = user.collections
        user.collect(Photo.query.get(1))
        collection = user.collections
        response = self.client.get(url_for('user.show_collections', username='common'))
        data = response.get_data(as_text=True)
        self.assertNotIn("No collection", data)

    def test_follow(self):
        # login required
        response = self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Please log in to access", data)

