# app/core/security.py
"""
安全相关功能
包括密码加密、JWT令牌生成和验证
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib
from app.config import settings
from app.core.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    密码哈希

    Args:
        password: 明文密码

    Returns:
        密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 令牌载荷数据
        expires_delta: 过期时间间隔

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # 生成令牌
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(
        data: Dict[str, Any],
        family_id: Optional[str] = None
) -> Tuple[str, str, datetime]:
    """
    创建刷新令牌

    Args:
        data: 令牌载荷数据
        family_id: 令牌家族ID

    Returns:
        (令牌字符串, JTI哈希, 过期时间)
    """
    to_encode = data.copy()

    # 生成唯一标识和家族ID
    jti = secrets.token_urlsafe(32)
    if not family_id:
        family_id = secrets.token_urlsafe(32)

    # 设置过期时间
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "family_id": family_id,
        "type": "refresh"
    })

    # 生成令牌
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    # 计算JTI哈希
    jti_hash = hashlib.sha256(jti.encode()).hexdigest()

    return encoded_jwt, jti_hash, expire


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        令牌载荷数据

    Raises:
        AuthenticationError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("令牌已过期")
    except JWTError as e:
        logger.error(f"JWT解码错误: {str(e)}")
        raise AuthenticationError("令牌无效")


def create_token_pair(
        user_id: int,
        tenant_id: int,
        extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    创建令牌对（访问令牌和刷新令牌）

    Args:
        user_id: 用户ID
        tenant_id: 租户ID
        extra_data: 额外数据

    Returns:
        包含access_token和refresh_token的字典
    """
    # 基础载荷数据
    token_data = {
        "user_id": user_id,
        "tenant_id": tenant_id
    }

    if extra_data:
        token_data.update(extra_data)

    # 创建访问令牌
    access_token = create_access_token(token_data)

    # 创建刷新令牌
    refresh_token, jti_hash, expire = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token_info": {
            "jti_hash": jti_hash,
            "expire": expire,
            "family_id": decode_token(refresh_token).get("family_id")
        }
    }


def generate_random_password(length: int = 12) -> str:
    """
    生成随机密码

    Args:
        length: 密码长度

    Returns:
        随机密码字符串
    """
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_token(token: str) -> str:
    """
    对令牌进行哈希

    Args:
        token: 原始令牌

    Returns:
        哈希值
    """
    return hashlib.sha256(token.encode()).hexdigest()