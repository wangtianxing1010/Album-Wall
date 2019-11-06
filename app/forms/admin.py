from wtforms import StringField, SubmitField, BooleanField, SelectField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email

from app.forms.user import EditProfileForm
from app.models import User, Role


class EditProfileAdminForm(EditProfileForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 50), Email()])
    role = SelectField("Role", coerce=int)
    active = BooleanField("Active")
    confirmed = BooleanField("Confirmed")
    submit = SubmitField()

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first(): # should be username=field.data?? Yes, the owner corrected it
            raise ValidationError("Username already in use.")

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("Email already in use.")