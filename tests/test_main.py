from flask import url_for

from app.extensions import db
from app.models import User, Photo, Notification, Comment, Tag
from tests.base import BaseTestCase


class MainTestCase(BaseTestCase):

    def test_index_page(self):
        res = self.client.get(url_for('main.index'))
        data = res.get_data(as_text=True)
        self.assertIn('Join Now', data)

        self.login()
        res = self.client.get(url_for('main.index'))
        data = res.get_data(as_text=True)
        self.assertIn("My Home", data)
        self.assertNotIn('Join Now', data)

    def test_explore_page(self):
        res = self.client.get(url_for('main.explore'))
        data = res.get_data(as_text=True)
        self.assertIn('Change', data)

    def test_search(self):
        # no query
        response = self.client.get(url_for('main.search', q=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Enter keyword about user, tag or photo', data)

        # search photo
        response = self.client.get(url_for('main.search', q='common'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Enter keyword about user, tag or photo', data)
        self.assertIn("No results", data)

        # search tab
        response = self.client.get(url_for('main.search', q='common', category='tag'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Enter keyword about user, tag or photo', data)
        self.assertIn("No results", data)

        # search user
        response = self.client.get(url_for('main.search', q='common', category='user'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Enter keyword about user, tag or photo', data)
        self.assertNotIn("No results", data)
        self.assertIn("Common User", data)

    def test_show_notifications(self):
        user = User.query.get(2)
        note1 = Notification(message='test 1', is_read=True, receiver=user)
        note2 = Notification(message='test 2', is_read=False, receiver=user)
        db.session.add_all([note1, note2])
        db.session.commit()

        self.login()
        res = self.client.get(url_for('main.show_notifications'))
        data = res.get_data(as_text=True)
        self.assertIn("test 1", data)
        self.assertIn("test 2", data)

        res = self.client.get(url_for('main.show_notifications', filter='unread'))
        data = res.get_data(as_text=True)
        self.assertNotIn("test 1", data)
        self.assertIn("test 2", data)

    def test_read_notification(self):
        user = User.query.get(2)
        note1 = Notification(message='test 1', receiver=user)
        note2 = Notification(message='test 2', receiver=user)
        db.session.add_all([note1, note2])
        db.session.commit()

        self.login(email='admin@test.com', password='123456')
        res = self.client.post(url_for('main.read_notification', notification_id=1))
        self.assertEqual(res.status_code, 403)

        self.logout()
        self.login()
        res = self.client.post(url_for('main.read_notification', notification_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Notification Archived", data)

        self.assertTrue(Notification.query.get(1).is_read)

    def test_read_all_notifications(self):
        user = User.query.get(2)
        note1 = Notification(message='test 1', receiver=user)
        note2 = Notification(message='test 2', receiver=user)
        db.session.add_all([note1, note2])
        db.session.commit()

        self.login()
        res = self.client.post(url_for('main.read_all_notifications'), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('All notifications archived', data)

        self.assertTrue(note1.is_read)
        self.assertTrue(note2.is_read)

        self.assertTrue(Notification.query.get(1).is_read)
        self.assertTrue(Notification.query.get(2).is_read)

    def test_show_photo(self):
        res = self.client.get(url_for('main.show_photo', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("test tag", data)
        self.assertIn("test comment body", data)
        self.assertNotIn('Delete', data)

        self.login('admin@test.com', '123456')
        res = self.client.get(url_for('main.show_photo', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Delete', data)

    def test_photo_next(self):
        admin = User.query.get(1)
        photo3 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 2", author=admin)
        photo4 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 3", author=admin)
        photo5 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 4", author=admin)
        db.session.add_all([photo3, photo4, photo5])
        db.session.commit()

        res = self.client.get(url_for('main.photo_next', photo_id=5), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 3", data)

        res = self.client.get(url_for('main.photo_next', photo_id=4), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 2", data)

        res = self.client.get(url_for('main.photo_next', photo_id=3), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 1", data)

        res = self.client.get(url_for('main.photo_next', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("This is already the last photo", data)

    def test_photo_previous(self):
        admin = User.query.get(1)
        photo3 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 2", author=admin)
        photo4 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 3", author=admin)
        photo5 = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                       description="Photo 4", author=admin)
        db.session.add_all([photo3, photo4, photo5])
        db.session.commit()

        res = self.client.get(url_for('main.photo_previous', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 2", data)

        res = self.client.get(url_for('main.photo_previous', photo_id=3), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 3", data)

        res = self.client.get(url_for('main.photo_previous', photo_id=4), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo 4", data)

        res = self.client.get(url_for('main.photo_previous', photo_id=5), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("This is already the first photo", data)

    def test_collect(self):
        photo = Photo(filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg',
                      description="Photo 3", author=User.query.get(2))
        db.session.add(photo)
        db.session.commit()
        self.assertEqual(photo.collectors, [])

        self.login()
        res = self.client.post(url_for('main.collect', photo_id=3), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Photo Collected', data)

        self.assertEqual(Photo.query.get(3).collectors[0].collector.name, "Common User")

        res = self.client.post(url_for('main.collect', photo_id=3), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Already Collected', data)

    def test_uncollect(self):
        self.login()
        self.client.post(url_for('main.collect', photo_id=1), follow_redirects=True)

        res = self.client.post(url_for('main.uncollect', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Photo Uncollected', data)

        res = self.client.post(url_for('main.uncollect', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Not collected yet', data)

    def test_report_comment(self):
        self.assertEqual(Comment.query.get(1).flag, 0)

        self.login()
        res = self.client.post(url_for('main.report_comment', comment_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Comment reported", data)
        self.assertEqual(Comment.query.get(1).flag, 1)

    def test_report_photo(self):
        self.assertEqual(Photo.query.get(1).flag, 0)

        self.login()
        res = self.client.post(url_for('main.report_photo', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn('Photo reported', data)
        self.assertEqual(Photo.query.get(1).flag, 1)

    def test_show_collectors(self):
        user = User.query.get(2)
        user.collect(Photo.query.get(1))
        res = self.client.get(url_for('main.show_collectors', photo_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("1 Collectors", data)
        self.assertIn("Common User", data)

    def test_edit_description(self):
        self.assertEqual(Photo.query.get(2).description, "Photo 2")

        self.login()
        res = self.client.post(url_for('main.edit_description', photo_id=2), data=dict(
            description="test edit description"
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertEqual("test edit description", Photo.query.get(2).description)
        self.assertIn("Description Updated", data)

    def test_new_comment(self):
        self.login()
        res = self.client.post(url_for('main.new_comment', photo_id=1), data=dict(
            body="common user test comment"
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Comment posted", data)
        self.assertEqual(Photo.query.get(1).comments[1].body, "common user test comment")

    def test_new_tag(self):
        self.login("admin@test.com", "123456")

        res = self.client.post(url_for('main.new_tag', photo_id=1), data=dict(
            tag="test tag from admin user"
        ), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Tag added", data)

        self.assertEqual(Photo.query.get(1).tags[1].name, "test")
        self.assertEqual(Photo.query.get(1).tags[2].name, "tag")
        self.assertEqual(Photo.query.get(1).tags[3].name, "from")
        self.assertEqual(Photo.query.get(1).tags[4].name, "admin")
        self.assertEqual(Photo.query.get(1).tags[5].name, "user")

    def test_allow_comment(self):
        self.login('admin@test.com', '123456')
        res = self.client.post(url_for('main.allow_comment', photo_id=2), follow_redirects=True)
        self.assertEqual(res.status_code, 403)

        self.logout()
        self.login()
        res = self.client.post(url_for('main.allow_comment', photo_id=2), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Comment Disabled", data)
        self.assertFalse(Photo.query.get(2).comment_allowed)

        res = self.client.post(url_for('main.allow_comment', photo_id=2), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Comment Enabled", data)
        self.assertTrue(Photo.query.get(2).comment_allowed)

    def test_reply_comment(self):
        self.login()
        res = self.client.get(url_for('main.reply_comment', comment_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Reply to", data)

    def test_delete_photo(self):
        self.login()
        res = self.client.post(url_for('main.delete_photo', photo_id=2), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Photo deleted", data)
        self.assertIn("Common User", data)

    def test_delete_comment(self):
        self.login('admin@test.com', '123456')
        res = self.client.post(url_for('main.delete_comment', comment_id=1), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Comment deleted", data)
        self.assertIn("Photo 1", data)

    def test_show_by_tag(self):
        res = self.client.get(url_for('main.show_by_tag', tag_id=1))
        data = res.get_data(as_text=True)
        self.assertIn("Order by time", data)

        res = self.client.get(url_for('main.show_by_tag', tag_id=1, order="by_collections"))
        data = res.get_data(as_text=True)
        self.assertIn("Order by collections", data)

    def test_delete_tag(self):
        photo = Photo.query.get(2)
        tag = Tag(name='test')
        photo.tags.append(tag)
        db.session.commit()

        self.login()
        res = self.client.post(url_for('main.delete_tag', photo_id=2, tag_id=2), follow_redirects=True)
        data = res.get_data(as_text=True)
        self.assertIn("Tag deleted", data)

        self.assertEqual(photo.tags, [])
        self.assertIsNone(Tag.query.get(2))
