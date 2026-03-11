from pathlib import Path


def is_running_from_source() -> bool:
    """
    Check if the application is running from source code.

    Returns:
        bool: True if running from source, False if running from installed package
    """
    return Path("pyproject.toml").exists()
