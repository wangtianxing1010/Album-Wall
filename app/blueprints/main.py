import os

from flask import render_template, Blueprint, current_app, request, send_from_directory, \
    abort, flash, redirect, url_for

from flask_login import login_required, current_user

from app.decorators import confirm_required, permission_required
from app.extensions import db
from app.models import User, Photo, Tag, Comment, Collect, Notification, Follow
from app.notifications import push_comment_notification, push_collect_notification
from app.utils import rename_image, resize_image, flash_errors, redirect_back
from app.forms.main import DescriptionForm, CommentForm, TagForm

from sqlalchemy.sql.expression import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/test')
def test():
    return render_template('test.html')


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['ALBUM_WALL_PHOTO_PER_PAGE']
        pagination = Photo.query.join(Follow, Follow.followed_id == Photo.author_id)\
            .filter(Follow.follower_id == current_user.id)\
            .order_by(Photo.timestamp.desc()).paginate(page, per_page)
        photos = pagination.items
    else:
        pagination = None
        photos = None
    tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
    return render_template('main/index.html', pagination=pagination, photos=photos, tag=tags)


@main_bp.route('/explore')
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUM_WALL_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/upload', methods=["POST", "GET"])
@login_required
@confirm_required
@permission_required("UPLOAD")
def upload():
    if request.method == "POST" and 'file' in request.files:
        f = request.args.get('file')
        filename = rename_image(f.filename)
        f.save(os.path.join(current_app.config['ALBUM_WALL_UPLOAD_PATH']), filename)
        filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
        filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])
        photo = Photo(
            filename=filename,
            filename_m=filename_m,
            filename_s=filename_s,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
    db.session.commit()
    return render_template('main/upload.html')


@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config['ALBUM_WALL_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.desc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    return render_template('main/photo.html', photo=photo, pagination=pagination, comments=comments,
                           comment_form=comment_form, description_form=description_form, tag_form=tag_form)


@main_bp.route("/photo/n/<int:photo_id>")
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.timestamp.desc()).first()

    if photo_n is None:
        flash("This is already the last photo", 'warning')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/photo/p/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id>photo_id).order_by(Photo.timestamp.asc()).first()

    if photo_p is None:
        flash("This is already the first photo", 'warning')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_p.id))


@main_bp.route('/collect/<int:photo_id>', methods=["POST"])
@login_required
@confirm_required
@permission_required("COLLECT")
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash("Already Collected", 'warning')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash("Photo Collected", 'success')
    if current_user != photo.author and photo.author.receive_collect_notifications:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash("Not collected yet", "warning")
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash("Photo Uncollected", 'success')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUM_WALL_COMMENT_PER_PAGE']
    pagination = Collect.query.with_parent(photo).paginate(page, per_page)
    collections = pagination.items  # collection.collector will be retrieved in the template
    return render_template('main/collectors.html', collections=collections, photo=photo, pagination=pagination)


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash("Comment reported", 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo.id))


@main_bp.route('/report/photo/<int:photo_id>', methods=["POST"])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash("Photo reported, Thanks", 'success')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/description', methods=["POST", "GET"])
@login_required
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description Updated', 'success')
    form.description.data = photo.description

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST', "GET"])
@login_required
@permission_required("COMMENT")
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get("page", 1, type=int)
    if not photo.comment_allowed:
        flash("Comment Disabled")
        return redirect(url_for('.show_photo', photo_id=photo_id, page=page))
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(photo=photo, body=body, author=author)

        replying_to_id = request.args.get('reply')
        if replying_to_id:
            comment.replying_to = Comment.query.get_or_404(replying_to_id)
            if comment.replying_to.author.receive_comment_notifications:
                push_comment_notification(photo_id=photo_id, receiver=comment.replying_to.author)
        db.session.add(comment)
        db.session.commit()
        flash("Comment posted", 'success')
        if current_user != photo.author and photo.author.receive_comment_notifications:
            push_comment_notification(photo_id, receiver=photo.author, page=page)
    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash("Tag added", 'success')
    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route("/allow_comment/<int:photo_id>", methods=['POST'])
@login_required
def allow_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    photo.comment_allowed = not photo.comment_allowed
    if photo.comment_allowed:
        flash("Comment Enabled", 'success')
    flash("Comment Disabled", 'success')
    db.session.commit()
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required("COMMENT")
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(url_for('.show_photo', photo_id=comment.photo.id, reply=comment_id,
                            author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/photo/<int:photo_id>', methods=["POST", "GET"])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):
        abort(403)

    db.session.delete(photo)
    db.session.commit()
    flash("Photo deleted.", 'warning')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id<photo_id).order_by(Photo.timestamp.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id>photo_id).order_by(Photo.timestamp.asc()).first()
        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))
        return redirect(url_for('.show_photo', photo_id=photo_p.id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/delete/comment/<int:comment_id>', methods=["POST", "GET"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author and not current_user.can("MODERATE"):
        abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted", 'warning')
    return redirect(url_for('.show_photo', photo_id=comment.photo.id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_by_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config['ALBUM_WALL_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collections':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collections'
    return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route("/delete/tag/<int:photo_id>/<int:tag_id>", methods=["POST", "GET"])
@login_required
def delete_tag(photo_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can("MODERATE"):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash("Tag deleted", 'warning')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUM_WALL_PHOTO_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notifications/read/<int:notification_id>', methods=["POST"])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash("Notification Archived", 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=["POST"])
@login_required
def read_all_notifications():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash("All notifications archived", 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash("Enter keyword about user, tag or photo", 'warning')
        return redirect_back()

    category = request.args.get("category", 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUM_WALL_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'photo':
        pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('main/search.html', page=page, results=results, q=q, pagination=pagination, category=category)