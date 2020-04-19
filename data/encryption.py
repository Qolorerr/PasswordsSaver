from cryptography.fernet import Fernet


def init_encryption():
    global cipher
    cipher = Fernet(bytes(open("db/key.txt", 'r').read().encode("UTF-8")))


def encryption(text):
    return cipher.encrypt(bytes(text.encode('UTF-8')))


def decryption(enc_text):
    return cipher.decrypt(bytes(enc_text)).decode('UTF-8')
