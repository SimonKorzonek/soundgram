
from flask_wtf import FlaskForm  # allows to use flask forms
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField  # importing field classes
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()], render_kw={"placeholder": "What do you think about this?", "rows": 1})
    submit = SubmitField('Send')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={"placeholder": "Title"})
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={"placeholder": "Say something about it", "rows": 6})
    content = FileField('Upload file', validators=[DataRequired(), FileAllowed(['mp3', 'mp4', 'jpg', 'png'])])
    submit = SubmitField('Upload')
