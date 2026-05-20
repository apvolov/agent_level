import math
from typing import List


class Segmenter:
    @staticmethod
    def split(data: bytes, segment_size: int) -> List[bytes]:
        """
        Разбивает бинарные данные на сегменты заданного размера.

        Args:
            data: бинарные данные тайла
            segment_size: максимальный размер одного сегмента в байтах

        Returns:
            Список байтовых сегментов
        """
        
        if not data:
            raise ValueError("Пустые данные — нечего сегментировать")

        total = len(data)
        num_segments = math.ceil(total / segment_size)
        segments = [
            data[i * segment_size : (i + 1) * segment_size]
            for i in range(num_segments)
        ]
        return segments
