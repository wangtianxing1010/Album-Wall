from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_dropzone import Dropzone
from flask_avatars import Avatars
from flask_whooshee import Whooshee


bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()
dropzone = Dropzone()
avatars = Avatars()
whooshee = Whooshee()


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    user = User.query.get(int(user_id))
    return user


login_manager.login_view = 'auth.login'
# login_manager.login_message = 'Your custom message'
login_manager.login_message_category = 'Please log in to access this page'

login_manager.refresh_view = 'auth.re_authenticate'
# login_manager.needs_refresh_message = "Your custom message'
login_manager.needs_refresh_message_category = 'warning'


class Guest(AnonymousUserMixin):

    @property
    def is_admin(self):
        return False

    def can(self, permission_name):
        return False


login_manager.anonymous_user = Guest