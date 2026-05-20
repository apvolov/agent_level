# Агентный уровень — Передача тайлов ДЗЗ

Веб-сервис на **FastAPI + Python 3.11**, реализующий агентный уровень распределённой системы передачи спутниковых тайлов.

## Архитектура

```
Транспортный уровень
       │  POST /input
       ▼
  Agent service  ──── getTileImage ──►  MinIO (Image Storage)
       │                                      │
       │◄─────────────── tile_data ───────────┘
       │
       │  SplitToSegments (по 3 МБ)
       │
       │  POST /transfer (×N сегментов)
       ▼
Транспортный уровень
```

## Быстрый старт

### 1. Запустить все сервисы

```bash
docker compose up --build
```

После старта будут доступны:

| Сервис | URL |
|---|---|
| Агентный уровень | http://localhost:8000 |
| Swagger UI агента | http://localhost:8000/docs |
| Заглушка транспорта | http://localhost:8001 |
| MinIO Web-консоль | http://localhost:9001 (admin: minioadmin/minioadmin) |

### 2. Загрузить тайлы в MinIO

Положите 16 файлов в папку `tiles/` с именами `tile_X_Y.png` (где X, Y от 0 до 3):

```
tiles/
  tile_0_0.png
  tile_0_1.png
  ...
  tile_3_3.png
```

Затем выполните:

```bash
pip install minio
python scripts/upload_tiles.py --tiles-dir ./tiles
```

Или загрузите через веб-консоль MinIO: http://localhost:9001 → бакет `tiles`.

### 3. Отправить тестовый запрос

```bash
curl -X POST http://localhost:8000/input \
  -H "Content-Type: application/json" \
  -d '{
    "time": 1716000000000,
    "sender": "Dima",
    "tile_x": 2,
    "tile_y": 3
  }'
```

Ожидаемый ответ:
```json
{"status": "ok", "message": "Запрос принят в обработку"}
```

### 4. Проверить логи заглушки транспорта

```bash
docker logs mock-transport -f
```

Вы увидите входящие сегменты:
```
[MOCK-TRANSPORT] Сегмент 1/4 тайла (2,3) | получено: 1/4 | error=False
[MOCK-TRANSPORT] Сегмент 2/4 тайла (2,3) | получено: 2/4 | error=False
...
[MOCK-TRANSPORT] ✅ Тайл (2,3) собран полностью → /tmp/received/tile_2_3_...png
```

Статистика буфера:
```bash
curl http://localhost:8001/stats
```

---

## API агентного уровня

### `POST /input`

Принять запрос на тайл от транспортного уровня.

**Тело запроса:**
```json
{
  "time": 1716000000000,
  "sender": "Dima",
  "tile_x": 2,
  "tile_y": 3
}
```

| Поле | Тип | Описание |
|---|---|---|
| `time` | integer | Unix timestamp (мс) — используется как ID сообщения |
| `sender` | string | Имя отправителя |
| `tile_x` | integer (0–3) | Координата X тайла |
| `tile_y` | integer (0–3) | Координата Y тайла |

**Ответ:** `200 OK` — немедленно, сегментация идёт в фоне.

---

### Формат сегмента (POST /transfer на транспортный уровень)

```json
{
  "time": 1716000000000,
  "tile_x": 2,
  "tile_y": 3,
  "total_segs": 4,
  "seq_num": 0,
  "error": false,
  "payload": "89504e470d0a..."
}
```

| Поле | Тип | Описание |
|---|---|---|
| `time` | integer | ID сообщения (из входящего запроса) |
| `tile_x` | integer | Координата X |
| `tile_y` | integer | Координата Y |
| `total_segs` | integer | Общее количество сегментов |
| `seq_num` | integer | Номер текущего сегмента (с 0) |
| `error` | boolean | Признак ошибки |
| `payload` | string | Бинарные данные сегмента в формате HEX |

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MINIO_ENDPOINT` | `minio:9000` | Адрес MinIO |
| `MINIO_ACCESS_KEY` | `minioadmin` | Логин MinIO |
| `MINIO_SECRET_KEY` | `minioadmin` | Пароль MinIO |
| `MINIO_BUCKET` | `tiles` | Имя бакета |
| `MINIO_SECURE` | `false` | HTTPS для MinIO |
| `TRANSPORT_URL` | `http://mock-transport:8001` | URL транспортного уровня |
| `SEGMENT_SIZE_BYTES` | `3145728` | Размер сегмента (3 МБ) |

Для подключения к реальному транспортному уровню измените `TRANSPORT_URL` в `docker-compose.yml`.

---

## Соглашение об именах тайлов в MinIO

Объекты хранятся с именами вида `tile_{x}_{y}.png`:

```
tile_0_0.png  tile_1_0.png  tile_2_0.png  tile_3_0.png
tile_0_1.png  tile_1_1.png  tile_2_1.png  tile_3_1.png
tile_0_2.png  tile_1_2.png  tile_2_2.png  tile_3_2.png
tile_0_3.png  tile_1_3.png  tile_2_3.png  tile_3_3.png
```
