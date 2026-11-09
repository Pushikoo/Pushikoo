"""
ImageService - Handle image URIs, store locally, and provide access links.
"""

import datetime
import hashlib
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from loguru import logger
from PIL import Image
from sqlmodel import select

from pushikoo.db import File as FileDB
from pushikoo.db import get_session
from pushikoo.util.setting import (
    FILE_DIR,
    IMAGE_LINK_DEFAULT_EXPIRE_SECOND,
    settings,
)
from pushikoo.service.base import InvalidInputException

REMOTE_CONNECT_TIMEOUT_SECONDS = 10
REMOTE_READ_TIMEOUT_SECONDS = 30
REMOTE_DOWNLOAD_MAX_SECONDS = 120
REMOTE_DOWNLOAD_MAX_BYTES = 50 * 1024 * 1024

# Format to MIME suffix mapping
FORMAT_TO_SUFFIX = {
    "JPEG": "jpeg",
    "PNG": "png",
    "GIF": "gif",
    "BMP": "bmp",
    "TIFF": "tiff",
    "WEBP": "webp",
}


class ImageService:
    _http_get = staticmethod(requests.get)

    @staticmethod
    def create(uri: str) -> str:
        """
        Process an image URI and return an access link.

        Args:
            uri: Image URI (file:/// or http(s)://)

        Returns:
            Access URL: BACKEND_BASE_HOST + /file/{uuid}
        """
        image_path: Path | None = None
        is_remote = urlparse(uri).scheme in ("http", "https")
        try:
            image_path = ImageService._resolve_uri_to_file(uri)
            file_hash = ImageService._calculate_hash(image_path)
            suffix = ImageService._detect_image_format(image_path)

            filename = f"{file_hash}.{suffix}"
            target_path = FILE_DIR / filename
            if not target_path.exists():
                shutil.copy2(image_path, target_path)
                logger.debug(f"Saved image to {target_path}")

            file_id = uuid.uuid4()
            expire_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=IMAGE_LINK_DEFAULT_EXPIRE_SECOND)

            with get_session() as session:
                file_record = FileDB(
                    id=file_id,
                    filename=filename,
                    expire_at=expire_at,
                )
                session.add(file_record)
                session.commit()
                logger.debug(f"Created file record: {file_id} -> {filename}")

            return f"{settings.BASE_HOST}/file/{file_id}"
        except Exception as e:
            logger.warning(f"ImageService.create failed for {uri}: {e}")
            return uri
        finally:
            if is_remote and image_path is not None:
                try:
                    image_path.unlink(missing_ok=True)
                except OSError as error:
                    logger.warning(
                        f"Failed to delete temporary image file {image_path}: {error}"
                    )

    @staticmethod
    def _resolve_uri_to_file(uri: str) -> Path:
        """
        Resolve URI to a local file path.
        Downloads remote files to a temp location if needed.
        """
        parsed = urlparse(uri)

        if parsed.scheme == "file":
            # file:/// URI - extract local path
            # On Windows: file:///C:/path -> C:/path
            # On Unix: file:///path -> /path
            local_path = parsed.path
            if (
                local_path.startswith("/")
                and len(local_path) > 2
                and local_path[2] == ":"
            ):
                # Windows path like /C:/path
                local_path = local_path[1:]
            return Path(local_path)

        elif parsed.scheme in ("http", "https"):
            started_at = time.monotonic()
            response = ImageService._http_get(
                uri,
                stream=True,
                timeout=(
                    REMOTE_CONNECT_TIMEOUT_SECONDS,
                    REMOTE_READ_TIMEOUT_SECONDS,
                ),
            )
            temp_path: Path | None = None
            try:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if (
                    content_length is not None
                    and int(content_length) > REMOTE_DOWNLOAD_MAX_BYTES
                ):
                    raise InvalidInputException(
                        f"Remote image exceeds {REMOTE_DOWNLOAD_MAX_BYTES} byte limit"
                    )

                suffix = Path(parsed.path).suffix or ""
                downloaded = 0
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    temp_path = Path(tmp.name)
                    for chunk in response.iter_content(chunk_size=8192):
                        if time.monotonic() - started_at > REMOTE_DOWNLOAD_MAX_SECONDS:
                            raise InvalidInputException(
                                "Remote image download exceeded "
                                f"{REMOTE_DOWNLOAD_MAX_SECONDS} second limit"
                            )
                        if chunk:
                            downloaded += len(chunk)
                            if downloaded > REMOTE_DOWNLOAD_MAX_BYTES:
                                raise InvalidInputException(
                                    "Remote image exceeds "
                                    f"{REMOTE_DOWNLOAD_MAX_BYTES} byte limit"
                                )
                            tmp.write(chunk)
                    if time.monotonic() - started_at > REMOTE_DOWNLOAD_MAX_SECONDS:
                        raise InvalidInputException(
                            "Remote image download exceeded "
                            f"{REMOTE_DOWNLOAD_MAX_SECONDS} second limit"
                        )
                return temp_path
            except Exception:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
                raise
            finally:
                close = getattr(response, "close", None)
                if close is not None:
                    close()

        elif not parsed.scheme or (
            len(parsed.scheme) == 1 and len(uri) > 1 and uri[1] == ":"
        ):
            # Plain local path, including Windows drive-letter paths.
            return Path(uri)

        else:
            raise InvalidInputException(f"Unsupported URI scheme: {parsed.scheme}")

    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _detect_image_format(file_path: Path) -> str:
        """Detect image format using PIL and return file suffix."""
        with Image.open(file_path) as img:
            fmt = img.format
            if fmt and fmt.upper() in FORMAT_TO_SUFFIX:
                return FORMAT_TO_SUFFIX[fmt.upper()]
            raise InvalidInputException(f"Unsupported image format: {fmt}")

    @staticmethod
    def get_file_by_id(file_id: uuid.UUID) -> FileDB | None:
        """Get file record by ID."""
        with get_session() as session:
            return session.exec(select(FileDB).where(FileDB.id == file_id)).first()
