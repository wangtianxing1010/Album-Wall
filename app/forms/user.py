from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, TextAreaField, ValidationError, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Regexp, EqualTo, Email
from flask_wtf.file import FileAllowed, FileField, FileRequired

from app.models import User


class EditProfileForm(FlaskForm):
    name = StringField("name", validators=[DataRequired(), Length(1, 30)])
    username = StringField('username', validators=[DataRequired(), Length(1, 30), Regexp('^[a-zA-Z0-9]*$',
                                                                                         message='Only a-z A-Z 0-9')])
    website = StringField("Website", validators=[Optional(), Length(0, 250)])
    location = StringField("City", validators=[Optional(), Length(0, 50)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(0, 250)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError("The username is already used")


class UploadAvatarForm(FlaskForm):
    image = FileField('Uplaod', validators=[FileRequired(), FileAllowed(['jpg','png'], 'jpg or png file')])
    submit = SubmitField()


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField("Crop and Update")


class ChangeEmailForm(FlaskForm):
    email = StringField("New Email", validators=[DataRequired(), Length(1, 50), Email()])
    submit = SubmitField()


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old password", validators=[DataRequired()])
    password = PasswordField("New password", validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField("Confirm password", validators=[DataRequired(), Length(8, 128)])
    submit = SubmitField()


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField("New comment")
    receive_collect_notification = BooleanField("New collect")
    receive_follow_notification = BooleanField("New follower")
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField("Make my collections public")
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError("Wrong username")