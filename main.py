import os
import time
import urllib
from os import listdir, stat, remove
from threading import Timer
from time import mktime, localtime
from smtplib import SMTPRecipientsRefused

import pyotp
import pyqrcode
from flask import Flask
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_restful import Api
from werkzeug.utils import redirect
from flask import render_template
from flask import make_response
from data import db_session
from data.add_pass_form import AddPasswordForm
from data.edit_password_form import EditPasswordForm
from data.login_form import LoginForm
from data.passwords import Password
from data.profile_form import ProfileForm
from data.register_form import RegisterForm
from data.send_mail import send_password, send_mail
from data.show_auth_qr_form import ShowAuthQRForm
from data.tags import Tag
from data.users import User
from data.search_password_form import SearchForm
from data.show_password_form import ShowPasswordForm
from data.encryption import encryption, decryption, init_encryption
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'af1f2ed264b7a6b18b84971091cbaceea33697bf3b80ad5cd495898c8ced0a2d09b1e8012a0' \
                           'b00868f5d6b6500a2cee7e591fbc2dd88f3f9a4caa2239d4576ac'
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)

init_encryption()


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')


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
        try:
            send_mail(form.email.data, 'Mail connection', 'All your passwords will be sent here')
        except SMTPRecipientsRefused:
            return render_template('register.html',
                                   message="This email doesn't exists",
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
        if form.email.data != '':
            try:
                send_mail(form.email.data, 'Mail connection', 'All your passwords will be sent here')
            except SMTPRecipientsRefused:
                return render_template('profile.html',
                                       message="This email doesn't exists",
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
            if user.authenticator_key is not None and user.authenticator_key[0] != '$':
                totp = pyotp.TOTP(user.authenticator_key)
                if not totp.verify(form.code.data):
                    return render_template('login.html',
                                           message="Wrong auth code",
                                           form=form,
                                           version=random.randint(0, 10 ** 5))
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
        password.hashed_password = encryption(form.password.data)
        password.tags_id = " " + ' '.join([str(i) for i in tags_id]) + " "
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


@app.route('/')
def preview():
    return render_template('preview.html', version=random.randint(0, 10 ** 5))


@app.route('/passwords_list', methods=['GET', 'POST'])
@login_required
def password_list():
    site_list = []
    form = SearchForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        info = form.tags.data.split()
        id_list = []
        for tag in info:
            id = session.query(Tag).filter(Tag.tag == tag).first()
            site = session.query(Password).filter(Password.site == tag, Password.user_id == current_user.id).first()
            if id is not None:
                id_list.append(id.id)
            elif site is not None:
                site_list.append({"site": site.site, "id": str(site.id)})
        for id in id_list:
            site = session.query(Password).filter(Password.user_id == current_user.id, Password.tags_id.like("% " + str(id) + " %")).first()
            print(site)
            if site is not None:
                site_list.append({"site": site.site, "id": str(site.id)})
    if not site_list:
        site_list = list(map(lambda x: {"site": x.site, "id": str(x.id)}, list(session.query(Password).filter(Password.user_id == current_user.id).all())))
    return render_template('pass_list.html', form=form, sites=site_list, version=random.randint(0, 10 ** 5))


@app.route('/passwords_list/<int:id>', methods=['GET', 'POST'])
@login_required
def show_password(id):
    form = ShowPasswordForm()
    session = db_session.create_session()
    password = session.query(Password).filter(Password.id == id, Password.user_id == current_user.id).first()
    if password is not None:
        site = password.site
        tags_id = password.tags_id.split()
        tags = ""
        for i in tags_id:
            tags += session.query(Tag).filter(Tag.id == i).first().tag + " "
    else:
        return redirect('/passwords_list')
    if form.validate_on_submit():
        site = password.site
        user_id = password.user_id
        email = session.query(User).filter(User.id == user_id).first().email
        password = decryption(session.query(Password).filter(Password.id == id, Password.user_id == current_user.id).first().hashed_password)
        send_password(email, site, password)
    return render_template('show_password.html', form=form, site=site, tags=tags, id=id, version=random.randint(0, 10 ** 5))


@app.route('/passwords_list/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_password(id):
    form = EditPasswordForm()
    session = db_session.create_session()
    password = session.query(Password).filter(Password.id == id, Password.user_id == current_user.id).first()
    if password is None:
        return redirect('/passwords_list')
    if form.validate_on_submit():
        if current_user.hash(form.acc_password.data) != current_user.hashed_password:
            return render_template('profile.html',
                                   message="Wrong old password",
                                   form=form,
                                   version=random.randint(0, 10 ** 5))
        if form.site.data != '':
            password.site = form.site.data
        if form.password.data != '':
            password.hashed_password = encryption(form.password.data)
        if form.tags.data != '':
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
            password.tags_id = " " + ' '.join([str(i) for i in tags_id]) + " "
        session.commit()
        return redirect('/passwords_list/{}'.format(str(id)))
    return render_template('edit_pass.html', form=form, id=id, version=random.randint(0, 10 ** 5))


@app.route('/passwords_list/delete/<int:id>')
@login_required
def delete_password(id):
    session = db_session.create_session()
    password = session.query(Password).filter(Password.id == id, Password.user_id == current_user.id).first()
    if password is not None:
        session.delete(password)
        session.commit()
    return redirect('/passwords_list')


@app.route('/add_authenticator', methods=['GET', 'POST'])
@login_required
def add_authenticator():
    if current_user.authenticator_key is None or current_user.authenticator_key[0] == '$':
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        user.authenticator_key = '$' + pyotp.random_base32()
        session.commit()
    return redirect('/show_auth_qr')


@app.route('/show_auth_qr', methods=['GET', 'POST'])
@login_required
def show_auth_qr():
    path = 'static/img/qr{}.png'.format(str(current_user.id))
    key = current_user.authenticator_key
    form = ShowAuthQRForm()
    if form.validate_on_submit():
        if key[0] == '$':
            session = db_session.create_session()
            user = session.query(User).filter(User.id == current_user.id).first()
            user.authenticator_key = key[1:]
            session.commit()
        return redirect('/start')

    if key is None:
        return redirect('/add_authenticator')
    if key[0] == '$':
        key = key[1:]
    data = 'PasswordsSaver:' + current_user.email
    url = pyotp.totp.TOTP(key).provisioning_uri(name=data)
    url = urllib.parse.unquote(url)
    big_code = pyqrcode.create(url)
    big_code.png(path, scale=6, module_color=[255, 255, 255, 255], background=[46, 46, 46, 255])
    time.sleep(1)
    timer = Timer(300, cleaner)
    timer.start()
    return render_template('show_auth_qr.html', form=form, qr_url=path)


def cleaner():
    path = 'static/img'
    files = listdir(path)
    for file in files:
        if 'qr' in file and '.png' in file:
            file_path = path + '/' + file
            mtime = stat(file_path).st_mtime
            if (mktime(localtime()) - mtime) // 60 >= 5:
                remove(file_path)


def show_auth_qr_mobile():
    form = ShowAuthQRForm()
    if form.validate_on_submit():
        return redirect('/start')

    key = current_user.authenticator_key
    if key is None:
        return redirect('/add_authenticator')

    data = 'PasswordsSaver:' + current_user.email
    return key, data


def main():
    db_session.global_init("db/passwords.sqlite")
    app.run(port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
