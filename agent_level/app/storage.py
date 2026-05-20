import asyncio
from minio import Minio

from .config import settings

import logging
logger = logging.getLogger(__name__)


class ImageStorage:
    _client: Minio = None

    @classmethod
    async def init(cls):
        """Инициализация клиента MinIO при старте приложения."""
        cls._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        exists = await asyncio.to_thread(cls._client.bucket_exists, settings.minio_bucket)
        if not exists:
            await asyncio.to_thread(cls._client.make_bucket, settings.minio_bucket)
            logger.info(f"[STORAGE] Бакет '{settings.minio_bucket}' создан")
        else:
            logger.info(f"[STORAGE] Подключено к бакету '{settings.minio_bucket}'")

    @classmethod
    async def get_tile(cls, row: int, col: int) -> bytes:
        """
        Получить бинарные данные тайла из MinIO.
        Имена объектов: tile_{row}_{col}.png
        """
        object_name = f"tile_{row}_{col}.png"
        logger.info(f"[STORAGE] Загружаем объект '{object_name}' из MinIO")

        def _fetch():
            response = cls._client.get_object(settings.minio_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data

        data = await asyncio.to_thread(_fetch)
        logger.info(f"[STORAGE] Получено {len(data)} байт для тайла ({row},{col})")
        return data