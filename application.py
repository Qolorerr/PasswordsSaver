import hashlib
from flask import Flask, request
import logging
import json
from data.users import User
from data.passwords import Password
from data import db_session
from random import choice
from data.encryption import decryption, init_encryption
from password_strength import PasswordStats


Users_in_session = dict()

app = Flask(__name__)


level = [0]


def global_init():
    global sessionStorage
    db_session.global_init("db/passwords.sqlite")
    logging.basicConfig(level=logging.INFO)
    sessionStorage = {}
    init_encryption()


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
    sessionStorage[user_id] = {
        'suggests': [
            "Покажи пароли",
            "Добавить новый пароль",
        ]
    }
    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
            ]
        }
        if user_id in list(Users_in_session.keys()):
            Users_in_session.pop(user_id, None)
        res['response']['text'] = 'Приветствуем вас в Хранители Паролей! Введите свой логин и пароль через пробел'
        return

    user_authorized = user_id in list(Users_in_session.keys())
    session = db_session.create_session()
    back = False
    if req['request']['original_utterance'].lower() in ["обратно"]:
        level[0] -= 1
        back = True
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
                level[0] = 1
                Users_in_session[user_id] = user.id
                res["response"]["text"] = "Авторизация прошла успешно!"
                res['response']['buttons'] = [{'title': "Покажи пароли", 'hide': True},
                                              {'title': "Проверить пароль на безопасность", 'hide': True}]
                return
            else:
                res["response"]["text"] = "Логин и/или пароль были введены не верно, проверьте правильность " \
                                          "написания логина и/или пароля"
                return
        else:
            res["response"]["text"] = 'Вы ввели не правильные данные. Введите 2 слова: логин и пароль, ' \
                                      'через пробел. Пример: "admin admin123", без кавычек'
            return
    elif req['request']['original_utterance'].lower() in ["покажи пароли", "список паролей"] or (back and level[0] == 1):
        level[0] = 2
        print_passwords(user_id, res)
    elif req['request']['original_utterance'].lower() in ["проверить пароль на безопасность"]:
        level[0] = 1
        res["response"]["text"] = "Введите пароль, который вы хотите проверить."
        res['response']['buttons'] = [{'title': "Покажи пароли", 'hide': True}]
    elif level[0] == 1:
        status = int(100 * PasswordStats(req['request']['original_utterance']).strength())
        st = ["Худший пароль в мире",
              "Очень слабый пароль",
              "Плохой выбор",
              "Сойдёт",
              "Средний",
              "Более или менее нормальный",
              "Лучше среднего",
              "Уверенная защита",
              "Очень хорошая защита",
              "Уровень защиты - ФБР",
              "Идеальный пароль!"]
        res["response"]["text"] = st[int(str(status)[0])] + "\n" + "Уровень защиты: " + str(status) + " из 100"
        res['response']['buttons'] = [{'title': "Покажи пароли", 'hide': True}]
    elif level[0] == 2:
        level[0] = 2
        print_password(user_id, res, req['request']['original_utterance'])
        res['response']['buttons'] = [{'title': "Обратно", 'hide': True}]
    elif back:
        res["response"]["text"] = "Попробуйте варианты ниже."
    else:
        print(req['request']['original_utterance'].lower())
        bad_data(res)


def bad_data(res):
    answers = ["Даже не знаю, что на это ответить. Попробуйте написать по-другому",
               "Возможно вы ввели что-то неправильно.",
               "Я такого не умею.",
               "Задача не выполнима. Измените свой запрос."]
    res["response"]["text"] = choice(answers)


def print_password(user_id, res, pass_ind):
    session = db_session.create_session()
    passwords = session.query(Password).filter(Password.user_id == Users_in_session[user_id])
    ans = ""
    if pass_ind.isdigit() is False:
        res["response"]["text"] = "Вы ввели не число"
    elif not(0 <= int(pass_ind) - 1 < len(list(passwords))):
        res["response"]["text"] = "Такого номера нет среди списка паролей"

    else:
        pass_ind = int(pass_ind)
        ans += "Site: " + passwords[pass_ind - 1].site + "\n" + "Password: " +\
               decryption(passwords[pass_ind - 1].hashed_password) + "\n"
        ans += 'Чтобы вернуться, введите "обратно"'
        res["response"]["text"] = ans


def print_passwords(user_id, res):
    session = db_session.create_session()
    passwords = session.query(Password).filter(Password.user_id == Users_in_session[user_id])
    sug = [{'title': "Проверить пароль на безопасность", 'hide': True}]
    if passwords is not None:
        site_list = []
        for i in passwords:
            site_list.append(i.site)
        s = ""
        for ind, site in enumerate(site_list):
            sug.append({'title': str(ind + 1), 'hide': True})
            mes = str(ind + 1) + ". " + site + "\n"
            s += mes
        if s == "":
            res["response"]["text"] = "У вас нет ни одного сохранённого пароля."
            res['response']['buttons'] = sug
            return
        s += "Введите номер пароля, информацию о котором вы хотите получить"
        res["response"]["text"] = s
        res['response']['buttons'] = sug
        return
    else:
        res["response"]["text"] = "У вас нет ни одного сохранённого пароля."


if __name__ == '__main__':
    global_init()
    app.run()
