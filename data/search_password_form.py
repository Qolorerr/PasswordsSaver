from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SearchForm(FlaskForm):
    tags = StringField()
    submit = SubmitField('Fing')
