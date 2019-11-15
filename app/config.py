import os
import sys

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


WIN = sys.platform.startswith('win')

if WIN:
    prefix = 'sqlite:///'
else:
    prefix = "sqlite:////"


class BaseConfig:
    ALBUM_WALL_ADMIN_EMAIL = os.getenv('ALBUM_WALL_ADMIN_EMAIL', 'n.wang.travel@gmail.com')
    ALBUM_WALL_PHOTO_PER_PAGE = 12
    ALBUM_WALL_COMMENT_PER_PAGE = 15
    ALBUM_WALL_NOTIFICATION_PER_PAGE = 20
    ALBUM_WALL_USER_PER_PAGE = 20
    ALBUM_WALL_MANAGE_PHOTO_PER_PAGE = 20
    ALBUM_WALL_MANAGE_USER_PER_PAGE = 30
    ALBUM_WALL_MANAGE_COMMENT_PER_PAGE = 30
    ALBUM_WALL_MANAGE_TAG_PER_PAGE = 50
    ALBUM_WALL_SEARCH_RESULT_PER_PAGE = 20

    ALBUM_WALL_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    ALBUM_WALL_PHOTO_SIZE = {'small': 400,
                         'medium': 800}
    ALBUM_WALL_PHOTO_SUFFIX = {
        ALBUM_WALL_PHOTO_SIZE['small']: '_s',  # thumbnail
        ALBUM_WALL_PHOTO_SIZE['medium']: '_m',  # display
    }

    AVATARS_SAVE_PATH = os.path.join(ALBUM_WALL_UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)

    BOOTSTRAP_SERVE_LOCAL = True

    SECRET_KEY = os.getenv("SECRET_KEY", 'longsecretstringisme')
    MAX_CONTENT_LENGTH = 3*1024*1024

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ALBUM_WALL_MAIL_SUBJECT_PREFIX = '[ALBUM Wall]'
    MAIL_SERVER = os.getenv("MAIL_SERVER") or 'localhost'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ("Album wall admin", MAIL_USERNAME)

    DROPZONE_ALLOWED_FILE_TYPE = 'image'
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True

    REDIS_URL = os.environ.get("REDIS_URL") or 'redis://'

    WHOOSHEE_MIN_STRING_LEN = 1


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data-dev.db')
    REDIS_URL = os.environ.get("REDIS_URL") or 'redis://localhost'


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    WHOOSHEE_MEMORY_STORAGE = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///"  # in-memory database


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", prefix + os.path.join(basedir, 'data.db'))


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class HerokuConfig(ProductionConfig):
    pass


config = {
    'default': DevelopmentConfig,
    "development": DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'heroku': HerokuConfig
}