import time
from typing import Dict, Optional
from pynput.keyboard import Controller
from loguru import logger
from ..config.models import Region


class Slot:
    def __init__(self, number: int, region: Region, delay: float):
        self.number = number
        self.region = region
        self.delay = delay
        self.items = 0
        self.active = True
        self.last_use = 0.0
        self.first_use = True

    def can_use(self, current_time: float) -> bool:
        time_since_last = current_time - self.last_use
        return (
            self.active
            and self.items > 0
            and (self.first_use or time_since_last >= max(self.delay, 1.0))  # Минимальный кулдаун 1 секунда
        )

    def use(self, keyboard: Controller, current_time: float) -> bool:
        if not self.can_use(current_time):
            logger.debug(f"Slot {self.number} not usable: items={self.items}, active={self.active}")
            return False
        keyboard.press(str(self.number))
        keyboard.release(str(self.number))
        self.items = max(0, self.items - 1)
        self.last_use = current_time
        self.first_use = False
        logger.info(f"Used slot {self.number}, items left: {self.items}")
        return True


class SlotManager:
    def __init__(self, regions: Dict[str, Region], delays: Dict[int, float]):
        self.slots = {
            num: Slot(num, regions.get(f"slot_{num}"), delays.get(num, 1.0))
            for num in [5, 6]
        }
        self.keyboard = Controller()
        self.global_cooldown = 1.0  # Глобальный кулдаун из игры
        self.last_use_time = 0.0

    def set_delay(self, slot: int, delay: float) -> None:
        if slot in self.slots:
            self.slots[slot].delay = delay
            logger.info(f"Slot {slot} delay set to {delay}")

    def set_active(self, slot: int, active: bool) -> None:
        if slot in self.slots:
            self.slots[slot].active = active
            logger.info(f"Slot {slot} {'activated' if active else 'deactivated'}")

    def update_items(self, slot: int, items: int) -> None:
        if slot in self.slots:
            self.slots[slot].items = items
            logger.debug(f"Slot {slot} items updated: {items}")

    def use_item(self) -> bool:
        current_time = time.time()
        if current_time - self.last_use_time < self.global_cooldown:
            logger.debug(f"Global cooldown active: {self.global_cooldown - (current_time - self.last_use_time):.2f}s left")
            return False

        # Проверяем слоты последовательно, чтобы не пытаться нажать одновременно
        for slot in [5, 6]:
            if self.slots[slot].use(self.keyboard, current_time):
                self.last_use_time = current_time
                return True
        logger.debug("No usable slots")
        return False