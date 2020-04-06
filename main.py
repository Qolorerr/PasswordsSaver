from flask import Flask
from flask_login import LoginManager, login_required, logout_user, login_user
from flask_restful import Api
from werkzeug.utils import redirect
from flask import render_template
from flask import make_response

from data import db_session
from data.login_form import LoginForm
from data.register_form import RegisterForm
from data.users import User

import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'af1f2ed264b7a6b18b84971091cbaceea33697bf3b80ad5cd495898c8ced0a2d09b1e8012a0' \
                           'b00868f5d6b6500a2cee7e591fbc2dd88f3f9a4caa2239d4576ac'
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.login == form.login.data).first()
        if user is not None:
            return render_template('register.html',
                                   message="This login already used",
                                   form=form)
        user = session.query(User).filter(User.email == form.email.data).first()
        if user is not None:
            return render_template('register.html',
                                   message="This email already used",
                                   form=form)
        if form.password.data != form.password_rep.data:
            return render_template('register.html',
                                   message="Passwords don't match",
                                   form=form)
        user = User()
        user.login = form.login.data
        user.email = form.email.data
        user.hashed_password = user.hash(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=False)
        return redirect("/")
    return render_template('register.html', title='Authorisation', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter((User.login == form.login.data) | (User.email == form.login.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Wrong login or password",
                               form=form)
    return render_template('login.html', title='Authorisation', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Когда сделаем регистрацию и вход, надо будет добавить сюда @login_required
@app.route('/start')
def start():
    response = make_response(render_template("main.html", version=random.randint(0, 10 ** 5)))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/login')
def login():
    response = make_response(render_template("login.html", version=random.randint(0, 10 ** 5)))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/signup')
def signup():
    response = make_response(render_template("signup.html", version=random.randint(0, 10 ** 5)))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


def main():
    db_session.global_init("db/passwords.sqlite")
    app.run(port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
