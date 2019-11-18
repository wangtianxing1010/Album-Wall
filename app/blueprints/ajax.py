from flask import render_template, Blueprint, jsonify
from flask_login import current_user

from app.models import User, Notification, Photo
from app.notifications import push_follow_notification, push_collect_notification

ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    # todo render_template ??
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1
    return jsonify(count=count)


@ajax_bp.route('/follow/<username>', methods=["POST"])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message="Login required"), 403

    if not current_user.confirmed:
        return jsonify(message='Account confirmation required'), 400

    if not current_user.can("FOLLOW"):
        return jsonify(message='No permission'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='Already followed'), 400

    current_user.follow(user)
    if user.receive_collect_notifications:
        push_follow_notification(follower=current_user, receiver=user)
    return jsonify(message="User followed")


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
# todo ?? login required decorator works here too or not
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='Not followed yet'), 400

    current_user.unfollow(user)
    return jsonify(message="User unfollowed")


@ajax_bp.route('/notifications-count/')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message="Login required"), 403
    count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count), 200  # todo ?? status is 200


@ajax_bp.route('/collect_notification/<int:photo_id>/', methods=["POST"])
def collect_notification(photo_id):
    receiver = Photo.query.get_or_404(photo_id).author
    push_collect_notification(collector=current_user, photo_id=photo_id, receiver=receiver)
    notification = receiver.notifications[0]
    return jsonify(message=notification.message, receiver=notification.receiver.name)


@ajax_bp.route('/collect/<int:photo_id>', methods=['POST'])
def collect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message="Login required"), 403
    if not current_user.confirmed:
        return jsonify(message="Account confirmation required"), 400
    if not current_user.can("COLLECT"):
        return jsonify(message="Permission required"), 403

    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        return jsonify(message="Already collected"), 400

    current_user.collect(photo)
    not_author = current_user != photo.author
    allow_notification = photo.author.receive_collect_notifications
    if current_user != photo.author and photo.author.receive_collect_notifications:
        push_collect_notification(current_user, photo_id, photo.author)
    return jsonify(message="Photo collected", not_author=not_author, allow_notification=allow_notification)


@ajax_bp.route('/<int:photo_id>/followers-count')
def collectors_count(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    count = len(photo.collectors)
    return jsonify(count=count)


@ajax_bp.route("/uncollect/<int:photo_id>", methods=["POST"])
def uncollect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message="Login required"), 403

    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        return jsonify(message="Not yet collected"), 400

    current_user.uncollect(photo)
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(current_user, photo_id, photo.author)
    return jsonify(message="Photo uncollected")

