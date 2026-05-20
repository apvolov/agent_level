import asyncio
import httpx
import base64
from fastapi import FastAPI
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from .config import settings
from .storage import ImageStorage
from .segmenter import Segmenter

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ImageStorage.init()
    yield


app = FastAPI(
    title="Агентный уровень — Передача тайлов ДЗЗ",
    description="Сервис агентного уровня: извлечение тайлов из MinIO и сегментированная передача на транспортный уровень.",
    version="1.0.0",
    lifespan=lifespan,
)


class InputRequest(BaseModel):
    sent_at: str = Field(..., description="Метка времени запроса")
    sender: str
    tile_x: int = Field(..., ge=0, le=3)
    tile_y: int = Field(..., ge=0, le=3)


@app.post("/input")
async def input_tile(req: InputRequest):
    logger.info(f"[INPUT] Запрос от '{req.sender}': тайл ({req.tile_x}, {req.tile_y}), sent_at={req.sent_at}")
    asyncio.create_task(_process_tile(req))
    return {"status": "ok", "message": "Запрос принят в обработку"}


async def _process_tile(req: InputRequest):
    try:
        tile_data = await ImageStorage.get_tile(req.tile_x, req.tile_y)
    except Exception as e:
        logger.error(f"[STORAGE] Ошибка получения тайла ({req.tile_x},{req.tile_y}): {e}")
        return

    # Сначала кодируем всё в base64
    tile_base64 = base64.b64encode(tile_data).decode("ascii")

    # Потом режем base64 строку на сегменты
    segments = Segmenter.split(tile_base64.encode("ascii"), settings.segment_size_bytes)
    total_segs = len(segments)
    logger.info(f"[SEGMENTER] Тайл ({req.tile_x},{req.tile_y}) разбит на {total_segs} сегментов")

    async with httpx.AsyncClient(timeout=10.0) as client:
        for seq_num, payload in enumerate(segments):
            body = {
                "sent_at": req.sent_at,
                "sender": req.sender,
                "tile_x": req.tile_x,
                "tile_y": req.tile_y,
                "total_segs": total_segs,
                "seq_num": seq_num + 1,
                "error": False,
                "payload": payload.decode("ascii"),
            }
            logger.info(
                f"[TRANSFER] Отправляем сегмент {seq_num+1}/{total_segs}: "
                f"размер payload={len(payload)} байт"
            )
            try:
                resp = await client.post(
                    f"{settings.transport_url}/transfer",
                    json=body,
                )
                logger.info(f"[TRANSFER] Сегмент {seq_num+1}/{total_segs} → статус {resp.status_code}")
            except Exception as e:
                logger.error(f"[TRANSFER] Ошибка отправки сегмента {seq_num}: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}