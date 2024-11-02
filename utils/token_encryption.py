import base64
import logging
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Функція для генерування ключа
def generate_key():
    # Генерування солі
    salt = os.urandom(16)
    # Вибір функції для KDF
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    # Генерування ключа
    key = kdf.derive(b'B!T7274')
    # Кодування ключа в base64
    encoded_key = base64.urlsafe_b64encode(key).decode('utf-8')
    return encoded_key


# Функція для шифрування
def encrypt_token(key, token):
    key = base64.urlsafe_b64decode(key)
    # Генерування нонсу
    nonce = os.urandom(12)
    # Шифрування
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, token.encode(), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode('utf-8')


# Функція для розшифрування
def decrypt_token(key, encrypted_token):
    try:
        key = base64.urlsafe_b64decode(key)
        encrypted_token = base64.urlsafe_b64decode(encrypted_token)
        nonce = encrypted_token[:12]
        encrypted = encrypted_token[12:]
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, encrypted, None)
        return decrypted.decode('utf-8')
    except Exception as e:
        logging.debug(e)
        return None  # Неправильне декодування


# Функція для шифрування обох токенів
def encrypt_tokens(key, access_token, refresh_token):
    combined_tokens = f"{access_token}||{refresh_token}"
    return encrypt_token(key, combined_tokens)


# Функція для розшифрування обох токенів
def decrypt_tokens(key, encrypted_tokens):
    combined_tokens = decrypt_token(key, encrypted_tokens)
    if combined_tokens:
        return combined_tokens.split("||")
    return None, None


def is_valid_token_format(token):
    return len(token) > 150
