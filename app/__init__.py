import os

import click
from flask.cli import FlaskGroup

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError
from flask_login import current_user
import rq
from redis import Redis

from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.user import user_bp
from app.blueprints.admin import admin_bp
from app.blueprints.ajax import ajax_bp

from app.extensions import db, mail, moment, bootstrap, login_manager, csrf, dropzone, avatars, whooshee
from app.config import config
from app.models import User, Permission, Role, Photo, Tag, Comment, Follow, Collect, Notification

import logging
from logging.handlers import RotatingFileHandler


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('app')

    app.config.from_object(config[config_name])
    click.echo("config: %s" % config_name)

    register_extensions(app)
    register_blueprints(app)
    register_shell_context(app)
    register_template_context(app)
    register_errorhandlers(app)
    register_commands(app)

    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue("flask-album-tasks", connection=app.redis)
    # todo add to Procfile
    # worker: rq worker -u $REDIS_URL flask-album-tasks

    if not app.debug and not app.testing:
        # Log to stdout config for heroku
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/flask_album_wall.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Album Wall startup")

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    avatars.init_app(app)
    csrf.init_app(app)
    dropzone.init_app(app)
    whooshee.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Photo=Photo, Tag=Tag,
                    Comment=Comment, Follow=Follow, Collect=Collect, Notification=Notification)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template("errors/400.html", description=e.description), 500  # 500??


# @click.group(cls=FlaskGroup, create_app=create_app)
# def cli():
#     pass

# commands registeration for application factory

# https://dormousehole.readthedocs.io/en/latest/cli.html#id9
# https://packaging.python.org/tutorials/packaging-projects/#console-scripts
# https://isudox.com/2016/08/29/running-flask-with-gunicorn-in-application-factory/

def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Drop the existing database before creating')
    def initdb(drop):
        """Initialize database"""
        if drop:
            click.confirm('This will delete the current database, continue?', abort=True)
            db.drop_all()
            click.echo('Dropped tables')
        db.create_all()
        click.echo('Initialized database')

    @app.cli.command()
    def init():
        """Initialize Album Wall application"""
        click.echo("Initializing the database..")
        db.create_all()  # why create again????

        click.echo("Initializing the permissions and roles...")
        Role.init_role()

        click.echo('Done')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10')
    @click.option('--photo', default=30, help="Quantity of photos, default is 30")
    @click.option('--tag', default=20, help="Quantity of photos, default is 20")
    @click.option('--comment', default=100, help='Quantity of photos, default is 200')
    @click.option('--collection', default=50, help="Quantity of collections, default is 50")
    @click.option("--follow", default=30, help="Quantity of follows, default is 30")
    def forge(user, photo, tag, comment, collection, follow):
        """generating fake data"""
        from app.fakes import fake_admin, fake_user, fake_photo, fake_tag, fake_comment, fake_collect,\
            fake_follow
        click.echo("database: %s" % db.__repr__())
        db.drop_all()  # Why drop and create again???
        # so that when you execute the command multiple times, there is only one copy of data
        click.echo("Initializing the database..")
        db.create_all()

        click.echo("Initializing the roles and permissions...")
        Role.init_role()

        click.echo('Done')

        click.echo("database: %s" % db.__repr__())

        click.echo("Generating fake administrator")
        fake_admin()
        click.echo("Generating %s fake users" % user)
        fake_user(user)
        click.echo("Generating %s fake follows" % follow)
        fake_follow(follow)
        click.echo("Generating %s fake tags" % tag)
        fake_tag(tag)
        click.echo("Generating %s fake photos" % photo)
        fake_photo(photo)
        click.echo("Generating %s fake comments" % comment)
        fake_comment(comment)
        click.echo("Generating %s fake collections" % collection)
        fake_collect(collection)
        click.echo("Done")
