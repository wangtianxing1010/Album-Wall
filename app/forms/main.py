from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class DescriptionForm(FlaskForm):
    description = StringField("description", validators=[Optional(), Length(0, 500)])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField("Add Tag (use space to seperate)", validators=[Optional(), Length(0, 64)])
    submit = SubmitField()


class CommentForm(FlaskForm):
    body = TextAreaField('Comment here', validators=[DataRequired(), Length(1, 200)])
    submit = SubmitField()