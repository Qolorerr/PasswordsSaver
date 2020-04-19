import hashlib
from flask import Flask, request
import logging
import json
from data.users import User
from data.passwords import Password
from data import db_session


Users_in_session = dict()

app = Flask(__name__)


logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
            ]
        }
        res['response']['text'] = 'Приветствуем вас в Хранители Паролей! Введите свой логин и пароль через пробел'
        return

    user_authorized = user_id in list(Users_in_session.keys())
    session = db_session.create_session()
    if user_authorized is False:
        ans = req['request']['original_utterance'].split()
        if len(ans) == 2:
            log = ans[0]
            pas = ans[1]
            h = hashlib.sha3_512()
            h.update(pas.encode('UTF-8'))
            pas_hash = h.hexdigest()
            user = session.query(User).filter(User.login == log, User.hashed_password == pas_hash).first()
            if user is not None:
                Users_in_session[user_id] = user.id
                res["response"]["text"] = "Авторизация прошла успешно!"
                return
            else:
                res["response"]["text"] = "Такого пользователя нет, проверьте правильность " \
                                          "написания логина и/или пароля"
                return
        else:
            res["response"]["text"] = 'Вы ввели не правильные данные. Введите 2 слова: логин и пароль, ' \
                                      'через пробел. Пример: "admin admin123"'
            return
    else:
        session = db_session.create_session()
        passwords = session.query(Password).filter(Password.user_id == Users_in_session[user_id])
        if passwords is not None:
            site_list = []
            for i in passwords:
                site_list.append(i.site)
            for ind, site in enumerate(site_list):
                mes = str(ind) + ". " + site + "\n"
                res["response"]["text"] += mes
            return
        else:
            res["response"]["text"] = "У вас нет ни одного сохранённого пароля."
    return


if __name__ == '__main__':
    app.run()
