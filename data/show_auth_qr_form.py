from flask_wtf import FlaskForm
from wtforms import SubmitField


class ShowAuthQRForm(FlaskForm):
    submit = SubmitField()
