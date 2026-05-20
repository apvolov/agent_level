"""
Скрипт нарезки спутникового снимка на сетку 4×4 тайлов.

Соглашение об именовании: tile_{row}_{col}.png
  row — строка  (0 = верхняя,  3 = нижняя)
  col — столбец (0 = левый,    3 = правый)

Результат:
  tile_0_0.png  tile_0_1.png  tile_0_2.png  tile_0_3.png
  tile_1_0.png  tile_1_1.png  tile_1_2.png  tile_1_3.png
  tile_2_0.png  tile_2_1.png  tile_2_2.png  tile_2_3.png
  tile_3_0.png  tile_3_1.png  tile_3_2.png  tile_3_3.png

Использование:
  python split_tiles.py --input snapshot.jpg --output ./tiles

Зависимости:
  pip install Pillow
"""

import argparse
import os
from PIL import Image


GRID_SIZE = 4  # сетка 4×4


def split_into_tiles(input_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    image = Image.open(input_path)
    width, height = image.size
    print(f"Исходное изображение: {width}×{height} px")

    # Размер одного тайла
    tile_w = width // GRID_SIZE
    tile_h = height // GRID_SIZE
    print(f"Размер тайла: {tile_w}×{tile_h} px")

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            left   = col * tile_w
            upper  = row * tile_h
            right  = left + tile_w
            lower  = upper + tile_h

            tile = image.crop((left, upper, right, lower))

            filename = f"tile_{row}_{col}.png"
            out_path = os.path.join(output_dir, filename)
            tile.save(out_path, format="PNG")

            size_kb = os.path.getsize(out_path) / 1024
            print(f"  ✅ {filename}  [{left},{upper} → {right},{lower}]  {size_kb:.1f} KB")

    print(f"\nГотово! 16 тайлов сохранены в '{output_dir}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Нарезка снимка на тайлы 4×4")
    parser.add_argument("--input",  required=True, help="Путь к исходному изображению")
    parser.add_argument("--output", default="./tiles", help="Папка для тайлов (по умолчанию: ./tiles)")
    args = parser.parse_args()

    split_into_tiles(args.input, args.output)
