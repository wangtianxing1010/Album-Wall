from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import logout_user, login_user, login_required, current_user, login_fresh, confirm_login

from app.emails import send_confirmation_email, send_reset_password_email
from app.extensions import db
from app.utils import redirect_back, generate_token, validate_token
from app.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from app.config import Operations
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.validate_password(form.password.data):
            if login_user(user, form.remember_me.data):
                flash("Login success", 'success')
                return redirect_back()
            else:
                flash("Your account is blocked", "danger")
                return redirect(url_for('main.index'))
        flash("Invalid email or password", 'warning')
    return render_template("auth/login.html", form=form)


@auth_bp.route('/re-authenticate', methods=["POST", "GET"])
@login_required
def re_authenticate():
    if login_fresh():  # How does this do ??
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit() and current_user.validate_password(form.password.data):
        confirm_login()  # How does this do ??
        return redirect_back()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout success", 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user=user, operation='confirm')
        send_confirmation_email(user=user, token=token)
        flash("Confirm email sent, check your inbox", 'info')
    return render_template("auth/register.html", form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if validate_token(user=current_user, operation=Operations.CONFIRM, token=token):
        flash("Account confirmed", 'success')
        return redirect(url_for('main.index'))

    else:
        flash("Invalid or expired token", 'danger')
        return redirect(url_for('.resend_confirm_email'))


@auth_bp.route('/resend-confirm-email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    token = generate_token(user=current_user, operation=Operations.CONFIRM)
    send_confirmation_email(user=current_user, token=token)
    flash("New email sent, check your inbox", 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forget-password', methods=['POST', 'GET'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            send_reset_password_email(user=user, token=token)
            flash("Password reset email sent, check your inbox", 'info')
            return redirect(url_for('.login'))
        flash("Invalid email", 'warning')
        return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=["POST", "GET"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            return redirect(url_for("main.index"))
        if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD, new_password=form.password.data):
            flash("Password updated", 'success')
            return redirect(url_for('.login'))
        else:
            flash("Invalid or expired link", "danger")
            return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)
