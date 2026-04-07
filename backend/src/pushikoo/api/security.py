from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from pushikoo.util.setting import settings


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire_minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})

    secret = settings.SSO_CLIENT_SECRET or "dev-secret"
    return jwt.encode(to_encode, secret, algorithm="HS256")
