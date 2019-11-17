from flask import url_for
import io

from app.models import User, Photo
from app.utils import generate_token
from app.config import Operations

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

    # todo model needs to be updated ??
    def test_follow(self):
        # login required
        response = self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Please log in to access", data)

        # confirmation required
        self.login('unconfirmed@test.com', '123456')
        response = self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn("Please confirm your account", data)

        # common user
        self.logout()
        self.login()
        response = self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("User followed", data)
        # already followed
        response = self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Already followed", data)
        # notification received
        self.assertEqual(len(User.query.get(1).notifications), 1)

    def test_unfollow(self):
        # login protection
        res = self.client.post(url_for('user.unfollow', username='admin'), follow_redirects=True)
        d = res.get_data(as_text=True)
        self.assertIn("Please log in to access", d)

        self.login()
        self.assertEqual(0, User.query.get(2).followed.count()-1)
        res = self.client.post(url_for('user.unfollow', username='admin'), follow_redirects=True)
        d = res.get_data(as_text=True)
        self.assertIn("Not yet followed", d)

        self.client.post(url_for('user.follow', username='admin'), follow_redirects=True)
        res = self.client.post(url_for('user.unfollow', username='admin'), follow_redirects=True)
        d = res.get_data(as_text=True)
        self.assertIn("User unfollowed", d)

    def test_show_followers(self):
        res = self.client.get(url_for('user.show_followers', username='common'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Common User's followers", data)
        self.assertIn("No followers", data)

        admin = User.query.get(1)
        admin.follow(User.query.get(2))

        res = self.client.get(url_for('user.show_followers', username='common'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Admin User", data)
        self.assertNotIn("No followers", data)

    def test_show_following(self):
        res = self.client.get(url_for('user.show_following', username='common'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Common User's following", data)
        self.assertIn("No followings", data)

        common = User.query.get(2)
        common.follow(User.query.get(1))

        res = self.client.get(url_for('user.show_following', username='common'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Admin User", data)
        self.assertNotIn("No followings", data)

    def test_edit_profile(self):
        self.login()
        res = self.client.post(url_for('user.edit_profile'), data=dict(
            username='newname',
            name="New Name"
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Profile updated", data)
        user = User.query.get(2)
        self.assertEqual(user.username, 'newname')
        self.assertEqual(user.name, "New Name")

    def test_change_avatar(self):
        self.login()
        res = self.client.get(url_for('user.change_avatar'))
        data = res.get_data(as_text=True)
        self.assertIn("Change Avatar", data)

    def test_upload_avatar(self):
        self.login()
        data = {'image': (io.BytesIO(b"abcdef"), 'test.jpg')}
        res = self.client.post(url_for('user.upload_avatar'), data=data, follow_redirects=True,
                               content_type='multipart/form-data')
        data = res.get_data(as_text=True)
        self.assertIn("Image upload, please crop", data)

    def test_change_password(self):
        self.login()
        user = User.query.get(2)
        self.assertTrue(user.validate_password("123456"))

        res = self.client.post(url_for('user.change_password'), data=dict(
            old_password='123456',
            password='newpassword',
            password2='newpassword'
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Password updated", data)
        self.assertTrue(user.validate_password("newpassword"))
        self.assertFalse(user.validate_password("123456"))

    def test_change_email(self):
        user = User.query.get(2)
        self.assertEqual(user.email, 'common@test.com')
        token = generate_token(user, Operations.CHANGE_EMAIL, new_email='new@test.com')

        self.login()
        res = self.client.get(url_for('user.change_email', token=token), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Email updated", data)
        self.assertEqual(user.email, 'new@test.com')

        res = self.client.get(url_for('user.change_email', token='bad'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Invalid or expired token", data)

    def test_notification_setting(self):
        # test turing off
        self.login()
        res = self.client.post(url_for('user.notification_setting'), data=dict(
            receive_follow_notifications = '',
            receive_collect_notifications='',
            receive_comment_notifications='',
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Setting updated", data)

        user = User.query.get(2)
        self.assertFalse(user.receive_collect_notifications)
        self.assertFalse(user.receive_comment_notifications)
        self.assertFalse(user.receive_follow_notifications)

        # todo
        # test no notifications received
        # self.logout()
        # self.login('admin@test.com', '123456789')
        # self.client.post(url_for('user.follow', user_id=2), follow_redirects=True)
        # self.client.post(url_for('main.comment', photo_id=2), data=dict(
        #     body='test comment from admin user'
        # ),follow_redirects=True)
        # self.client.post(url_for('main.collect', photo_id=2), follow_redirects=True)
        # self.assertEqual(len(user.notifications), 0)

    def test_privacy_setting(self):
        self.login()
        res = self.client.post(url_for('user.privacy_setting'), data=dict(
            public_collections = ''
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Privacy setting updated", data)

        user = User.query.get(2)
        self.assertFalse(user.public_collections)
        self.assertEqual(user.public_collections, False)

        self.logout()
        res = self.client.get(url_for('user.show_collections', username='common'))
        data = res.get_data(as_text=True)
        self.assertIn("Common User's collection", data)
        self.assertIn("This user's collections was private.", data)

    def test_delete_account(self):
        self.login()
        res = self.client.post(url_for('user.delete_account'), data=dict(
            username = 'common'
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Your are kicked out, goodbye", data)
        self.assertIsNone(User.query.get(2))