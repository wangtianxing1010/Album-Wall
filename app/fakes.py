import os
import random

from PIL import Image
from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Photo, Tag, Comment, Notification
from flask import current_app

fake = Faker()


def fake_admin():
    admin = User(
        name='N wang',
        username='n.wang',
        email='n.wang.travel@gmail.com',
        bio=fake.sentence(),
        website=fake.url(),
        confirmed=True
    )
    admin.set_password('123456789')
    notification = Notification(message='Hello, welcome to Album Wall.', receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    moderator = User(email="moderator@test.com", name="Moderator User", username='admin', confirmed=True)
    moderator.set_password('123456789')
    moderator.set_role("Moderator")

    common_user = User(email="common@test.com", name="Common User", username='common', confirmed=True)
    common_user.set_password('123456789')

    unconfirmed_user = User(email="unconfirmed@test.com", name="Unconfirmed", username='unconfirmed', confirmed=False)
    unconfirmed_user.set_password('123456789')
    locked_user = User(email="locked@test.com", name="Locked User", username='locked', confirmed=True,
                       locked=True)
    locked_user.set_password('123456789')
    locked_user.lock()

    blocked_user = User(email="blocked@test.com", name="Blocked User", username='blocked', confirmed=True,
                        active=False)
    blocked_user.set_password('123456789')

    for c in range(count-5):
        user = User(
            name=fake.name(),
            username=fake.user_name(),
            email=fake.email(),
            bio=fake.sentence(),
            location=fake.city(),
            website=fake.url(),
            member_since=fake.date_this_decade(),
            confirmed=True
        )
        user.set_password('123456789')
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_photo(count=30):
    # photo
    upload_path = current_app.config['ALBUM_WALL_UPLOAD_PATH']
    for i in range(count):
        print i
        filename = "random_%d.jpg" % i
        r = lambda: random.randint(128, 255)
        img = Image.new(mode="RGB", size=(800, 800), color=(r(), r(), r()))
        img.save(os.path.join(upload_path, filename))

        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year()
        )
        # tag
        for j in range(random.randint(1, 5)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in photo.tags:
                photo.tags.append(tag)

        db.session.add(photo)
    db.session.commit()


def fake_follow(count=30):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.follow(User.query.get(random.randint(1, User.query.count())))
        db.session.commit()


def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Photo.query.get(random.randint(1, User.query.count())))
    db.session.commit()


def fake_comment(count=100):
    for i in range(count):
        comment = Comment(
            body=fake.sentence(),
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year(),
            photo=Photo.query.get(random.randint(1, Photo.query.count()))
        )
        db.session.add(comment)
    db.session.commit()
