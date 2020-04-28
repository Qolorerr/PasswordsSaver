from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField


class EditPasswordForm(FlaskForm):
    site = StringField('Site')
    password = PasswordField('Password')
    tags = StringField('Tags')
    acc_password = StringField('Account password')
    submit = SubmitField('Edit password')
