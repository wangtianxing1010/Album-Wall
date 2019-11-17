from flask import url_for

from tests.base import BaseTestCase
from app.models import User, Photo


class AjaxTestCase(BaseTestCase):

    def test_get_profile(self):
        res = self.client.get(url_for('ajax.get_profile', user_id=1))
        data = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Admin User", data)

    # todo follow testing
    def test_follow(self):
        pass

    def test_followers_count(self):
        pass

    def test_unfollow(self):
        pass

    def test_notifications_count(self):
        # login protection
        res = self.client.get(url_for('ajax.notifications_count'))
        data = res.get_json()
        self.assertEqual(res.status_code, 403)
        self.assertEqual("Login required", data['message'])

        # admin user collect common user's photo
        user = User.query.get(1)
        user.collect(Photo.query.get(2))
        # common user should receive notification
        self.login()
        common = User.query.get(2)
        res = self.client.get(url_for('ajax.notifications_count'))
        data = res.get_json()
        noti = len(common.notifications)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, data['count'])

    def test_collectors_count(self):
        # no collectors
        res = self.client.get(url_for('ajax.collectors_count', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(0, data['count'])

        # 1 collector
        self.login()
        user = User.query.get(2)
        user.collect(Photo.query.get(1))
        res = self.client.get(url_for('ajax.collectors_count', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, data['count'])

    def test_collect(self):
        # login protection
        res = self.client.post(url_for('ajax.collect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 403)
        self.assertEqual("Login required", data['message'])
        # unconfirmed user
        self.login('unconfirmed@test.com', '123456')
        res = self.client.post(url_for('ajax.collect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Account confirmation required", data['message'])
        # todo No Permission for COLLECT
        # collect successfully
        self.logout()
        self.login()
        res = self.client.post(url_for('ajax.collect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual("Photo collected", data['message'])
        # photo already collected
        res = self.client.post(url_for('ajax.collect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Already collected", data['message'])


    def uncollect(self):
        # login protection
        res = self.client.post(url_for('ajax.uncollect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 403)
        self.assertEqual("Login required", data['message'])
        # not collected yet
        self.login()

        res = self.client.post(url_for('ajax.uncollect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Not yet collected", data['message'])
        # uncollected successfully
        user = User.query.get(2)
        user.collect(Photo.query.get(1))
        res = self.client.post(url_for('ajax.uncollect', photo_id=1))
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual("Photo uncollected", data['message'])
