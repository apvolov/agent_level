"""
Заглушка транспортного уровня для тестирования агентного уровня в изоляции.

Принимает POST /transfer, логирует каждый сегмент и собирает статистику.
Когда все сегменты одного тайла получены — сохраняет итоговый файл в /tmp/received/.
"""

import os
import time
from collections import defaultdict
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [MOCK-TRANSPORT] %(message)s")
logger = logging.getLogger(__name__)

os.makedirs("/tmp/received", exist_ok=True)

app = FastAPI(title="Mock Transport Level")

# Хранилище сегментов: ключ = (time, tile_x, tile_y)
_buffer: dict = defaultdict(dict)


class TransferRequest(BaseModel):
    time: str  # было int, теперь str
    tile_x: int
    tile_y: int
    total_segs: int
    seq_num: int
    error: bool = False
    payload: Optional[str] = None


@app.post("/transfer", summary="Принять сегмент тайла от агентного уровня")
async def transfer(req: TransferRequest):
    key = (req.time, req.tile_x, req.tile_y)
    _buffer[key][req.seq_num] = req.payload

    received = len(_buffer[key])
    logger.info(
        f"Сегмент {req.seq_num + 1}/{req.total_segs} тайла ({req.tile_x},{req.tile_y}) "
        f"| получено: {received}/{req.total_segs} | error={req.error}"
    )

    # Если собрали все сегменты — сохраняем файл для проверки
    if received == req.total_segs:
        try:
            segments = [_buffer[key][i] for i in range(req.total_segs)]
            full_data = b"".join(bytes.fromhex(s) for s in segments)
            out_path = f"/tmp/received/tile_{req.tile_x}_{req.tile_y}_{req.time}.png"
            with open(out_path, "wb") as f:
                f.write(full_data)
            logger.info(f"✅ Тайл ({req.tile_x},{req.tile_y}) собран полностью → {out_path} ({len(full_data)} байт)")
            del _buffer[key]
        except Exception as e:
            logger.error(f"Ошибка сборки тайла: {e}")

    return {"status": "ok"}


@app.get("/stats", summary="Статистика буфера (сколько сегментов ожидает сборки)")
async def stats():
    return {
        str(k): {"received_segments": len(v)}
        for k, v in _buffer.items()
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
