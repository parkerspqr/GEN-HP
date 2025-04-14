import json
from pathlib import Path
from typing import Optional, Dict # <--- Добавить Dict
import mss # <--- Добавить импорт mss
from .models import Config, Settings, Region
from loguru import logger


class ConfigManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        # Убедимся, что директория config существует
        self.config_dir = base_path / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.config_dir / "settings.json"
        self.regions_file = self.config_dir / "regions.json"

    def load_config(self) -> Config:
        settings = self.load_settings()
        regions = self.load_regions()
        config = Config(settings=settings, regions=regions, base_path=self.base_path)
        # Валидация может происходить внутри Config или здесь, если необходимо
        # Пример простой проверки:
        required_regions = {"hp", "slot_5", "slot_6"}
        if not required_regions.issubset(config.regions.keys()):
             logger.warning(f"Missing required regions: {required_regions - set(config.regions.keys())}. Check config/regions.json or run configuration.")
             # Возможно, стоит не возвращать default, а требовать конфигурации
             # return self.get_default_config() # Или вызвать UI для настройки
        return config

    def load_settings(self) -> Settings:
        default_settings = Settings()
        if not self.settings_file.exists():
            logger.warning(f"Settings file not found: {self.settings_file}. Using default settings.")
            # Сохраняем дефолтные настройки при первом запуске или отсутствии файла
            self.save_settings(default_settings)
            return default_settings
        try:
            with self.settings_file.open("r") as f:
                data = json.load(f)
                # Используем getattr для безопасного доступа к полям default_settings
                return Settings(
                    hp_threshold=data.get("hp_threshold", default_settings.hp_threshold),
                    check_interval_stable=data.get("check_interval_stable", default_settings.check_interval_stable),
                    check_interval_healing=data.get("check_interval_healing", default_settings.check_interval_healing),
                    check_interval_idle=data.get("check_interval_idle", default_settings.check_interval_idle),
                    # Обработка словаря 'slot_delays' слиянием с дефолтным
                    slot_delays={**default_settings.slot_delays, **data.get("slot_delays", {})},
                )
        except (json.JSONDecodeError, TypeError, ValueError) as e: # Добавлен TypeError
            logger.error(f"Failed to load or parse settings file {self.settings_file}: {e}. Using default settings.")
            # В случае ошибки парсинга, возвращаем дефолтные
            return default_settings

    def load_regions(self) -> Dict[str, Region]:
        default_regions = {} # Или можно определить дефолтные регионы здесь
        if not self.regions_file.exists():
             logger.warning(f"Regions file not found: {self.regions_file}. No regions loaded. Please configure regions.")
             return default_regions
        try:
            # Используем 'with' для управления контекстом sct
            with mss.mss() as sct:
                 # Предполагается, что monitors[1] - это основной монитор.
                 # monitors[0] содержит размеры всех мониторов вместе.
                 monitor = sct.monitors[1]
                 w, h = monitor["width"], monitor["height"]

            if w <= 0 or h <= 0:
                 logger.error(f"Invalid screen dimensions detected: width={w}, height={h}. Cannot load regions.")
                 return default_regions

            with self.regions_file.open("r") as f:
                data = json.load(f)

            regions = {}
            required_keys = {"hp", "slot_5", "slot_6"} # Ключи, которые мы ожидаем

            for key in required_keys:
                if key in data and isinstance(data[key], dict):
                    region_data = data[key]
                    # Проверяем наличие необходимых ключей в данных региона
                    if all(k in region_data for k in ["left", "top", "width", "height"]):
                        try:
                            # Преобразуем относительные координаты в абсолютные
                            regions[key] = Region(
                                left=int(float(region_data["left"]) * w),
                                top=int(float(region_data["top"]) * h),
                                width=int(float(region_data["width"]) * w),
                                height=int(float(region_data["height"]) * h),
                            )
                        except (ValueError, TypeError) as conversion_error:
                             logger.warning(f"Invalid numeric data for region '{key}' in {self.regions_file}: {conversion_error}. Skipping region.")
                    else:
                        logger.warning(f"Missing coordinate keys for region '{key}' in {self.regions_file}. Skipping region.")
                else:
                    logger.warning(f"Region '{key}' not found or invalid format in {self.regions_file}.")

            return regions

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e: # Добавлены KeyError, TypeError
            logger.error(f"Failed to load or parse regions file {self.regions_file}: {e}. No regions loaded.")
            return default_regions
        except Exception as e: # Ловим другие возможные ошибки mss и т.д.
             logger.error(f"An unexpected error occurred during region loading: {e}")
             return default_regions

    def save_config(self, config: Config) -> None:
        self.save_settings(config.settings)
        self.save_regions(config.regions)

    def save_settings(self, settings: Settings) -> None:
        try:
            # Убедимся, что директория существует перед записью
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with self.settings_file.open("w") as f:
                # Преобразуем settings в dict для dump
                settings_dict = {
                     "hp_threshold": settings.hp_threshold,
                     "check_interval_stable": settings.check_interval_stable,
                     "check_interval_healing": settings.check_interval_healing,
                     "check_interval_idle": settings.check_interval_idle,
                     "slot_delays": settings.slot_delays,
                }
                json.dump(settings_dict, f, indent=4)
            logger.info(f"Settings saved to {self.settings_file}")
        except (IOError, TypeError) as e: # Уточняем типы ошибок
            logger.error(f"Failed to save settings to {self.settings_file}: {e}")

    def save_regions(self, regions: Dict[str, Region]) -> None:
        if not regions:
             logger.warning("Attempted to save an empty regions dictionary. Skipping save.")
             # Возможно, стоит удалить файл или оставить как есть
             # if self.regions_file.exists(): self.regions_file.unlink()
             return
        try:
            # Убедимся, что директория существует перед записью
            self.regions_file.parent.mkdir(parents=True, exist_ok=True)
            with mss.mss() as sct:
                 # Используем тот же монитор, что и при загрузке
                 monitor = sct.monitors[1]
                 w, h = monitor["width"], monitor["height"]

            # Проверка на нулевые размеры экрана
            if w <= 0 or h <= 0:
                logger.error(f"Invalid screen dimensions detected: width={w}, height={h}. Cannot save regions.")
                return

            data = {}
            for key, region in regions.items():
                 # Проверка валидности данных региона перед сохранением
                 if not isinstance(region, Region) or any(v < 0 for v in [region.left, region.top, region.width, region.height]):
                      logger.warning(f"Invalid data for region '{key}'. Skipping saving this region.")
                      continue
                 # Конвертация абсолютных координат в относительные
                 data[key] = {
                    "left": region.left / w,
                    "top": region.top / h,
                    "width": region.width / w,
                    "height": region.height / h,
                 }

            if not data:
                 logger.warning("No valid regions to save after filtering.")
                 return

            with self.regions_file.open("w") as f:
                json.dump(data, f, indent=4)
            logger.info(f"Regions saved to {self.regions_file}")
        except (IOError, TypeError, ZeroDivisionError) as e: # Уточняем типы ошибок
            logger.error(f"Failed to save regions to {self.regions_file}: {e}")
        except Exception as e: # Ловим другие возможные ошибки mss и т.д.
             logger.error(f"An unexpected error occurred during region saving: {e}")


    def get_default_config(self) -> Config:
        logger.info("Returning default configuration.")
        return Config(
            settings=Settings(),
            regions={}, # По умолчанию регионы не заданы
            base_path=self.base_path,
        )
