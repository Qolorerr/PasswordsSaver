from cryptography.fernet import Fernet


def init_encryption():
    global cipher
    cipher = Fernet(open('db/key.txt', 'r').read())


def encryption(text):
    return cipher.encrypt(bytes(text.encode('UTF-8')))


def decryption(enc_text):
    return cipher.decrypt(bytes(enc_text)).decode('UTF-8')
