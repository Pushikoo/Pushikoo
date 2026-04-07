from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from pushikoo.api.spa import router as sparouter
from pushikoo.api.v1 import oauth_router as v1_oauth_router
from pushikoo.api.v1 import router as v1_router
from pushikoo.api.v1.file import router as file_router
from pushikoo.service.adapter import adapter_container_app
from pushikoo.util.setting import settings

apirouter = APIRouter(prefix="/api")
apirouter.include_router(v1_oauth_router)
apirouter.include_router(v1_router)


def create_app() -> FastAPI:
    _fastapi_kwargs: dict = {}
    if settings.ENVIRONMENT == "production":
        _fastapi_kwargs["docs_url"] = None
        _fastapi_kwargs["redoc_url"] = None

    app = FastAPI(**_fastapi_kwargs)
    app.include_router(apirouter)
    app.include_router(file_router)
    app.mount("/ext", adapter_container_app)
    app.include_router(sparouter)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
    )

    @app.exception_handler(Exception)
    async def internal_server_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )

    return app


app = create_app()
