from datetime import datetime, timedelta
import hashlib
from typing import Optional
from jose import JWTError, JWT
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = JWT.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) 

def verify_signature(timestamp: str, nonce: str, body: str, secret_key: str, signature: str) -> bool:
    """
    验证请求签名
    
    Args:
        timestamp (str): 请求时间戳
        nonce (str): 随机数
        body (str): 请求体
        secret_key (str): 密钥
        signature (str): 待验证的签名
        
    Returns:
        bool: 签名是否有效
    """
    content = f"{timestamp}{nonce}{body}{secret_key}"
    expected_signature = hashlib.sha256(content.encode()).hexdigest()
    return signature == expected_signature