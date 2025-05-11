import hashlib
import hmac
import os
import base64
import time

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + pwd_hash).decode()

def check_password(password: str, hashed: str) -> bool:
    data = base64.b64decode(hashed.encode())
    salt, pwd_hash = data[:16], data[16:]
    check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hmac.compare_digest(pwd_hash, check_hash)

def authenticate(username: str, password: str) -> str:
    # 演示用，实际应查数据库
    if username == "user" and password == "password":
        # 简单token
        token = base64.b64encode(f"{username}:{int(time.time())}".encode()).decode()
        return token
    return None

__all__ = ["authenticate", "hash_password", "check_password"]
