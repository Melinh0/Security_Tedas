# api/utils.py
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import hashlib

def get_encryption_key():
    secret_key = settings.SECRET_KEY.encode('utf-8')
    return hashlib.sha256(secret_key).digest()

def encrypt_file(file_path):
    key = get_encryption_key()
    iv = get_random_bytes(16)
    
    with open(file_path, 'rb') as f:
        plaintext = f.read()
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    
    with open(file_path, 'wb') as f:
        f.write(iv + ciphertext)

def decrypt_file(file_path):
    key = get_encryption_key()
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    iv = data[:16]
    ciphertext = data[16:]
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    return plaintext