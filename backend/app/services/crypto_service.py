"""
============================================================
加密服务模块 - 敏感数据加密/解密
应用场景：API密钥等敏感字段的数据库静态加密
加密算法：Fernet (AES-128-CBC + HMAC-SHA256)
核心原则：密钥不出环境变量，服务端加密存储，返回时脱敏
============================================================
"""
import os
from cryptography.fernet import Fernet, MultiFernet
from typing import Optional

# ============================================================
# 密钥管理
# ============================================================

def _get_encryption_key() -> bytes:
    """
    从环境变量获取加密密钥
    若未设置则生成一个（⚠️ 生成后需固定，否则已加密数据无法解密）
    """
    key = os.environ.get("DATA_ENCRYPTION_KEY", "")
    if key:
        return key.encode()

    # 开发环境：从文件读取或自动生成
    key_file = "data/.encryption_key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read().strip()

    # 首次启动：自动生成并持久化（开发用，生产务必从环境变量注入）
    new_key = Fernet.generate_key()
    os.makedirs("data", exist_ok=True)
    with open(key_file, "wb") as f:
        f.write(new_key)
    return new_key


_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """懒加载 Fernet 实例"""
    global _fernet
    if _fernet is None:
        key = _get_encryption_key()
        _fernet = Fernet(key)
    return _fernet


# ============================================================
# 加密/解密接口
# ============================================================

def encrypt_value(plaintext: str) -> str:
    """
    加密字符串，返回 base64 密文（含 Fernet token 前缀）
    空字符串返回空字符串
    """
    if not plaintext:
        return ""
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """
    解密字符串，返回明文
    空字符串返回空字符串
    解密失败返回 "[DECRYPTION_FAILED]"
    """
    if not ciphertext:
        return ""
    try:
        f = _get_fernet()
        plain = f.decrypt(ciphertext.encode("utf-8"))
        return plain.decode("utf-8")
    except Exception:
        return "[DECRYPTION_FAILED]"


# ============================================================
# 工具函数
# ============================================================

def mask_key(key: str) -> str:
    """
    脱敏显示密钥：前6位 + **** + 后4位
    例: "sk-abc123def456ghi789" → "sk-abc****i789"
    """
    if not key:
        return ""
    if len(key) <= 10:
        return key[:3] + "***"
    return key[:6] + "****" + key[-4:]


def is_key_masked(value: str) -> bool:
    """判断密钥是否已被脱敏（含 ****）"""
    return "****" in value
