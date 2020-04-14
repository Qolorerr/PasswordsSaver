from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class AddPasswordForm(FlaskForm):
    site = StringField('Site', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    tags = StringField('Tags')
    submit = SubmitField('Add')
