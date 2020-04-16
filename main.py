from flask import Flask, jsonify
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_restful import Api
from werkzeug.utils import redirect
from flask import render_template
from flask import make_response

from data import db_session
from data.add_pass_form import AddPasswordForm
from data.login_form import LoginForm
from data.passwords import Password
from data.profile_form import ProfileForm
from data.register_form import RegisterForm
from data.tags import Tag
from data.users import User
from data.search_password_form import SearchForm

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


@app.route('/signup', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.login == form.login.data).first()
        if user is not None:
            return render_template('register.html',
                                   message="This login already used",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        user = session.query(User).filter(User.email == form.email.data).first()
        if user is not None:
            return render_template('register.html',
                                   message="This email already used",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        if form.password.data != form.password_rep.data:
            return render_template('register.html',
                                   message="Passwords don't match",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        user = User()
        user.login = form.login.data
        user.email = form.email.data
        user.hashed_password = user.hash(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=False)
        return redirect("/start")
    return render_template('register.html', title='Authorisation', form=form, version=random.randint(0, 10 ** 5))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if current_user.hash(form.password.data) != current_user.hashed_password:
            return render_template('profile.html',
                                   message="Wrong old password",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        user = session.query(User).filter(User.login == form.login.data).first()
        if user is not None:
            return render_template('profile.html',
                                   message="This login already used",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        user = session.query(User).filter(User.email == form.email.data).first()
        if user is not None:
            return render_template('profile.html',
                                   message="This email already used",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        if form.new_password.data != form.new_password_rep.data:
            return render_template('profile.html',
                                   message="Passwords don't match",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        user = session.query(User).filter(User.id == current_user.id).first()
        if form.login.data != '':
            user.login = form.login.data
        if form.email.data != '':
            user.email = form.email.data
        if form.new_password.data != '':
            user.hashed_password = current_user.hash(form.new_password.data)
        session.commit()
        return redirect("/start")
    return render_template('profile.html', title='Authorisation', form=form, version=random.randint(0, 10 ** 5))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter((User.login == form.login.data) | (User.email == form.login.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/start")
        return render_template('login.html',
                               message="Wrong login or password",
                               form=form,
                               version=random.randint(0, 10 ** 5))
    return render_template('login.html', title='Authorisation', form=form, version=random.randint(0, 10 ** 5))


@app.route('/add_password', methods=['GET', 'POST'])
@login_required
def add_pass():
    form = AddPasswordForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        tags_id = []
        for tag in form.tags.data.split():
            old_tag = session.query(Tag).filter(Tag.tag == tag).first()
            if old_tag is None:
                new_tag = Tag()
                new_tag.tag = tag
                session.add(new_tag)
                session.commit()
                tags_id.append(session.query(Tag).filter(Tag.tag == tag).first().id)
            else:
                tags_id.append(old_tag.id)
        password = Password()
        password.user_id = current_user.id
        password.site = form.site.data
        password.hashed_password = form.password.data
        password.tags_id = ' '.join([str(i) for i in tags_id])
        session.add(password)
        session.commit()
        return redirect('/start')
    return render_template('add_pass.html', title='Add password', form=form, version=random.randint(0, 10 ** 5))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/start')
@login_required
def start():
    response = make_response(render_template("main.html", version=random.randint(0, 10 ** 5)))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/passwords_list', methods=['GET', 'POST'])
@login_required
def password_list():
    form = SearchForm()
    if form.validate():
        tags = form.tags.data.split()
    return render_template('pass_list.html', form=form, version=random.randint(0, 10 ** 5))


def main():
    db_session.global_init("db/passwords.sqlite")
    app.run(port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
