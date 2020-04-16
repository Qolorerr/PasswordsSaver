from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length


class RegisterForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    password_rep = PasswordField('Repeat password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Register')
