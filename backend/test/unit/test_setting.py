from pushikoo.util.setting import Settings


def test_cors_local():
    settings = Settings(_env_file=None, ENVIRONMENT="local")
    assert settings.CORS_ORIGINS == ["*"]


def test_cors_production():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        BASE_HOST="https://example.com",
        CORS_ORIGINS=["https://api.example.com"],
    )
    assert "https://api.example.com" in settings.CORS_ORIGINS
    assert "https://example.com" in settings.CORS_ORIGINS


def test_backend_host_production():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        BASE_HOST="https://example.com",
    )
    assert settings.BACKEND_BASE_HOST == "https://example.com"


def test_backend_host_local():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="local",
        BACKEND_BASE_HOST="http://localhost:9000",
    )
    assert settings.BACKEND_BASE_HOST == "http://localhost:9000"
