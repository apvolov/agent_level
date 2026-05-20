from pydantic_settings import BaseSettings

_MB = 1024 * 1024
_DEFAULT_SEGMENT_SIZE_MB = 0.1


class Settings(BaseSettings):
    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "tiles"
    minio_secure: bool = False

    # Транспортный уровень
    transport_url: str = "http://mock-transport:8090"

    segment_size_bytes: int = int(_DEFAULT_SEGMENT_SIZE_MB * _MB)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
