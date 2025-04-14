import asyncio
from paddleocr import PaddleOCR
import numpy as np
from typing import Optional, Dict
from loguru import logger
import time 
from .preprocessor import Preprocessor


class OCREngine:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.preprocessor = Preprocessor(debug)
        self.reader = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            det_model_name="en_PP-OCRv4_mobile_det",
            rec_model_name="en_PP-OCRv4_mobile_rec",
            rec_char_type="en",
            det_db_unclip_ratio=2.0,
            use_mps=True,
        )
        self.hp_cache: Optional[int] = None
        self.slot_caches: Dict[int, int] = {5: 0, 6: 0}
        self.slot_last_update: Dict[int, float] = {5: 0.0, 6: 0.0}
        self.max_hp = 150
        self.max_attempts = 4
        self.update_interval = 2.0  # Слоты обновляются раз в 2 секунды

    async def process(self, img: np.ndarray, is_slot: bool, region_name: str) -> Optional[int]:
        logger.debug(f"OCR processing {region_name}")
        if np.all(img == 0):
            logger.warning(f"Black image for {region_name}")
            return None

        processed = self.preprocessor.process(img, region_name)
        for attempt in range(self.max_attempts):
            try:
                results = self.reader.ocr(processed, cls=True)
                if not results or not results[0]:
                    logger.debug(f"No OCR results for {region_name}, attempt {attempt + 1}")
                    await asyncio.sleep(0.1)
                    continue

                text = results[0][0][1][0].strip()
                logger.debug(f"Raw OCR text for {region_name}: '{text}'")

                if is_slot:
                    if text.startswith("x") and text[1:].isdigit():
                        value = int(text[1:])
                        if 0 <= value <= 999:
                            return value
                    # Пустой слот или неверный формат
                    return 0
                else:
                    if text.isdigit():
                        value = int(text)
                        if 0 <= value <= self.max_hp:
                            return value
                    logger.debug(f"Invalid HP text for {region_name}: '{text}'")
                    return None
            except Exception as e:
                logger.error(f"OCR attempt {attempt + 1} failed for {region_name}: {e}")
                await asyncio.sleep(0.1)
        logger.warning(f"OCR failed after {self.max_attempts} attempts for {region_name}")
        return 0 if is_slot else None

    async def update_hp(self, img: np.ndarray) -> Optional[int]:
        value = await self.process(img, is_slot=False, region_name="HP Region")
        if value is not None:
            self.hp_cache = value
            logger.info(f"HP updated: {value}")
        return self.hp_cache

    async def update_slot(self, slot: int, img: np.ndarray) -> int:
        current_time = time.time()
        if (
            current_time - self.slot_last_update[slot] < self.update_interval
            and self.slot_caches[slot] > 0
        ):
            logger.debug(f"Slot {slot} cache used: {self.slot_caches[slot]}")
            return self.slot_caches[slot]

        value = await self.process(img, is_slot=True, region_name=f"Slot {slot} Region")
        if value is None:
            # Повторные попытки для пустого слота
            for attempt in range(self.max_attempts - 1):
                await asyncio.sleep(0.5 / self.max_attempts)  # Распределяем попытки на 2 секунды
                value = await self.process(img, is_slot=True, region_name=f"Slot {slot} Region")
                if value is not None:
                    break

        self.slot_caches[slot] = value or 0
        self.slot_last_update[slot] = current_time
        logger.info(f"Slot {slot} updated: {self.slot_caches[slot]}")
        return self.slot_caches[slot]