from urllib.parse import quote

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from pushikoo.util.setting import settings

_bearer_scheme = HTTPBearer(auto_error=False)
COOKIE_NAME = "access_token"


async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    return await _verify_token(request, credentials)


async def verify_token_or_login_redirect(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    try:
        return await _verify_token(request, credentials)
    except HTTPException as exc:
        if (
            exc.status_code == status.HTTP_401_UNAUTHORIZED
            and "text/html" in request.headers.get("accept", "")
        ):
            redirect_path = request.url.path
            if request.url.query:
                redirect_path = f"{redirect_path}?{request.url.query}"

            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": f"/login?redirect={quote(redirect_path, safe='')}"},
            ) from exc
        raise


async def _verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if settings.ENVIRONMENT == "local" and settings.LOCAL_AUTH_DISABLED:
        return "whatever"

    token: str | None = None
    if (
        credentials is not None
        and credentials.scheme
        and credentials.scheme.lower() == "bearer"
    ):
        token = credentials.credentials.strip()

    if not token:
        cookie_token = request.cookies.get(COOKIE_NAME)
        if cookie_token:
            token = cookie_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    valid_keys = settings.SECRET_TOKENS

    if token in valid_keys:
        return token

    if settings.SSO_CLIENT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SSO_CLIENT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            sub = payload.get("sub")
            if not sub:
                raise InvalidTokenError("missing sub")
            return str(sub)
        except InvalidTokenError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
