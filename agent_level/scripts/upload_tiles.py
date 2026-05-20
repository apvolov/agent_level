#!/usr/bin/env python3
"""
Скрипт загрузки тайлов в MinIO.

Использование:
    python scripts/upload_tiles.py --tiles-dir ./my_tiles

Ожидаемые имена файлов в папке:
    tile_0_0.png, tile_0_1.png, ..., tile_3_3.png  (16 файлов)

Зависимости (установить локально):
    pip install minio
"""

import argparse
import os
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT",  "localhost:9000")
MINIO_ACCESS    = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET    = os.getenv("MINIO_BUCKET",     "tiles")


def upload(tiles_dir: str):
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)

    # Создать бакет если нет
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"✅ Бакет '{MINIO_BUCKET}' создан")

    uploaded = 0
    missing  = []

    for x in range(4):
        for y in range(4):
            filename    = f"tile_{x}_{y}.png"
            local_path  = os.path.join(tiles_dir, filename)

            if not os.path.exists(local_path):
                missing.append(filename)
                continue

            client.fput_object(MINIO_BUCKET, filename, local_path, content_type="image/png")
            size = os.path.getsize(local_path)
            print(f"  ↑ {filename}  ({size / 1024:.1f} KB)")
            uploaded += 1

    print(f"\n✅ Загружено: {uploaded}/16 тайлов")
    if missing:
        print(f"⚠️  Не найдено: {missing}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Загрузка тайлов в MinIO")
    parser.add_argument(
        "--tiles-dir", default="./tiles",
        help="Папка с файлами tile_X_Y.png (по умолчанию: ./tiles)"
    )
    args = parser.parse_args()
    upload(args.tiles_dir)
