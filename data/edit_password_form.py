from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class EditPasswordForm(FlaskForm):
    site = StringField('Site')
    password = PasswordField('Password')
    tags = StringField('Tags')
    acc_password = StringField('Account password', validators=[DataRequired()])
    submit = SubmitField('Edit password')
