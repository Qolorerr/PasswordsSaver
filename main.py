from flask import Flask
from flask_login import LoginManager, login_required, logout_user
from flask_restful import Api
from werkzeug.utils import redirect
from flask import render_template
from flask import make_response

from data import db_session
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/start')
def start():
    response = make_response(render_template("main.html", version=random.randint(0, 10 ** 5)))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


def main():
    db_session.global_init("db/passwords.sqlite")
    app.run(port=5000, host='192.168.1.114')


if __name__ == '__main__':
    main()
