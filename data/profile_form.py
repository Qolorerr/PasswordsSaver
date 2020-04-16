from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length


class ProfileForm(FlaskForm):
    login = StringField('Login', validators=[Length(min=4, max=25)])
    email = StringField('Email')
    password = PasswordField('Old password')
    new_password = PasswordField('New password', validators=[Length(min=8, max=30)])
    new_password_rep = PasswordField('Repeat new password', validators=[Length(min=8, max=30)])
    submit = SubmitField('Change')
