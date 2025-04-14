import asyncio
import time
from enum import Enum
from typing import Dict, Optional
from loguru import logger
from ..config.models import Config, Region
from ..capture.screen import ScreenCapture
from ..ocr.engine import OCREngine
from ..utils.platform import WindowChecker
from .slots import SlotManager


class State(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    HEALING = "healing"
    PAUSED = "paused"


class AutomationCore:
    def __init__(self, config: Config, debug: bool = True):
        self.config = config
        self.debug = debug
        self.state = State.IDLE
        self.capture = ScreenCapture()
        self.ocr = OCREngine(debug)
        self.slots = SlotManager(config.regions, config.settings.slot_delays)
        self.window_checker = WindowChecker()
        self.hp: Optional[int] = None
        self.is_window_active = False
        self.should_stop = False
        self.last_slot_update = 0.0
        self.slot_update_interval = 2.0
        logger.debug(f"AutomationCore initialized: debug={debug}, regions={self.config.regions}")

    async def update_config(self, config: Config) -> None:
        self.config = config
        self.slots = SlotManager(config.regions, config.settings.slot_delays)
        logger.info("Config updated")

    async def run(self) -> None:
        self.state = State.MONITORING
        self.should_stop = False
        logger.info("Automation started")
        try:
            while not self.should_stop:
                logger.debug("Run loop iteration")
                await self.step()
                await asyncio.sleep(0.1)  # Увеличил паузу для надёжности
        except Exception as e:
            logger.error(f"Run loop failed: {e}", exc_info=True)
        finally:
            self.state = State.IDLE
            logger.info("Automation stopped")

    async def step(self) -> None:
        logger.debug("Step started")
        try:
            self.is_window_active = self.window_checker.is_app_active("Rust")
            logger.debug(f"Rust window active: {self.is_window_active}")

            if not self.is_window_active:
                if self.state != State.PAUSED:
                    self.state = State.PAUSED
                    logger.info("Rust window inactive, paused")
                return

            if self.state == State.PAUSED:
                self.state = State.MONITORING
                logger.info("Rust window active, resumed")

            if not all(key in self.config.regions for key in ["hp", "slot_5", "slot_6"]):
                logger.error("Missing regions, stopping")
                self.should_stop = True
                return

            interval = (
                self.config.settings.check_interval_healing
                if self.state == State.HEALING
                else self.config.settings.check_interval_stable
                if self.hp and self.hp >= self.config.settings.hp_threshold
                else self.config.settings.check_interval_idle
            )
            logger.debug(f"Check interval: {interval}")

            # Обновляем HP
            logger.debug(f"Capturing HP region: {self.config.regions['hp']}")
            hp_img = await self.capture.capture_region(self.config.regions["hp"])
            if hp_img is None:
                logger.warning("Failed to capture HP image")
                return
            self.hp = await self.ocr.update_hp(hp_img)
            logger.debug(f"HP detected: {self.hp}")

            if self.hp is None:
                logger.warning("HP not detected, skipping step")
                return

            # Обновляем слоты
            current_time = time.time()
            if current_time - self.last_slot_update >= self.slot_update_interval:
                logger.debug("Updating slots")
                slot_tasks = []
                for slot in [5, 6]:
                    logger.debug(f"Capturing slot_{slot} region: {self.config.regions[f'slot_{slot}']}")
                    slot_img = await self.capture.capture_region(self.config.regions[f"slot_{slot}"])
                    if slot_img is not None:
                        slot_tasks.append(self.ocr.update_slot(slot, slot_img))
                    else:
                        logger.warning(f"Failed to capture slot_{slot} image")
                if slot_tasks:
                    slot_results = await asyncio.gather(*slot_tasks, return_exceptions=True)
                    for slot, result in zip([5, 6], slot_results):
                        if isinstance(result, int):
                            self.slots.update_items(slot, result)
                            logger.debug(f"Slot {slot} items: {result}")
                        else:
                            logger.warning(f"Failed to update slot {slot}: {result}")
                self.last_slot_update = current_time

            # Логируем состояние
            slot_5_items = self.slots.slots.get(5, SlotManager.Slot(5)).items
            slot_6_items = self.slots.slots.get(6, SlotManager.Slot(6)).items
            logger.info(f"State: {self.state.value}, HP: {self.hp}, Slots: {slot_5_items}/{slot_6_items}")

            # Проверяем HP
            if self.hp < self.config.settings.hp_threshold and self.hp > 0:
                self.state = State.HEALING
                logger.debug("HP below threshold, attempting to heal")
                if self.slots.use_item():
                    logger.info("Healing triggered")
                    self.last_slot_update = 0.0
                else:
                    logger.debug("No items available for healing")
            else:
                self.state = State.MONITORING
                logger.debug("HP stable, monitoring")
        except Exception as e:
            logger.error(f"Step failed: {e}", exc_info=True)

    def stop(self) -> None:
        self.should_stop = True
        logger.debug("Stop signal received")

    def set_slot_active(self, slot: int, active: bool) -> None:
        self.slots.set_active(slot, active)
        logger.debug(f"Slot {slot} active: {active}")

    def set_slot_delay(self, slot: int, delay: float) -> None:
        self.slots.set_delay(slot, delay)
        logger.debug(f"Slot {slot} delay set to {delay}")