# Техническая документация AutoHPrust

Этот документ содержит подробное описание архитектуры и кодовой базы проекта **AutoHPrust** — приложения для автоматизации использования предметов в игре Rust на основе мониторинга уровня здоровья (HP).

Документация предназначена для разработчиков и AI-агентов, которым необходимо понять работу каждой функции и класса для внесения изменений или расширения функционала.

## Общая архитектура

Приложение построено на модульной архитектуре:
- **Automation (`src/automation`)**: Ядро логики. Управляет циклом мониторинга, проверкой условий и выполнением действий.
- **Capture (`src/capture`)**: Отвечает за захват изображения с экрана и выделение областей.
- **OCR (`src/ocr`)**: Распознавание текста (чисел) на изображениях с помощью PaddleOCR.
- **Config (`src/config`)**: Управление настройками и конфигурационными файлами (JSON).
- **GUI (`src/gui`)**: Графический интерфейс на Tkinter для взаимодействия с пользователем.
- **Utils (`src/utils`)**: Вспомогательные утилиты (логирование, проверка активного окна).

---

## Модуль `src/automation`

### Файл `src/automation/core.py`

#### Класс `AutomationCore`
Центральный класс, управляющий автоматизацией. Связывает захват экрана, OCR и логику использования слотов.

*   **`__init__(self, config: Config, debug: bool = True)`**
    *   Инициализирует компоненты: захват экрана, OCR, менеджер слотов, проверку окна.
    *   *Аргументы*:
        *   `config`: Объект конфигурации.
        *   `debug`: Флаг режима отладки.

*   **`async update_config(self, config: Config) -> None`**
    *   Обновляет текущую конфигурацию и пересоздает менеджер слотов.
    *   *Аргументы*: `config` - Новая конфигурация.

*   **`async run(self) -> None`**
    *   Запускает основной цикл мониторинга. Работает пока `should_stop` не станет True.
    *   Логика: вызывает `step()` в цикле с паузой. Обрабатывает исключения.

*   **`async step(self) -> None`**
    *   Выполняет одну итерацию цикла мониторинга.
    *   Логика:
        1. Проверяет активность окна "Rust". Если не активно — пауза.
        2. Проверяет наличие регионов (hp, slot_5, slot_6).
        3. Определяет интервал проверки в зависимости от состояния.
        4. Захватывает изображение HP и распознает значение.
        5. Периодически обновляет информацию о предметах в слотах (раз в 2 сек).
        6. Если HP ниже порога — переходит в режим HEALING и пытается использовать предмет.
        7. Если HP в норме — режим MONITORING.

*   **`stop(self) -> None`**
    *   Останавливает цикл мониторинга.

*   **`set_slot_active(self, slot: int, active: bool) -> None`**
    *   Включает/выключает использование указанного слота.

*   **`set_slot_delay(self, slot: int, delay: float) -> None`**
    *   Устанавливает задержку (кулдаун) для слота.

### Файл `src/automation/slots.py`

#### Класс `Slot`
Представляет отдельный слот инвентаря.

*   **`__init__(self, number: int, region: Region, delay: float)`**
    *   Инициализация слота.

*   **`can_use(self, current_time: float) -> bool`**
    *   Проверяет, можно ли использовать слот (активен, есть предметы, прошел кулдаун).
    *   *Возвращает*: `bool`

*   **`use(self, keyboard: Controller, current_time: float) -> bool`**
    *   Имитирует нажатие клавиши слота.
    *   *Аргументы*:
        *   `keyboard`: Контроллер клавиатуры pynput.
        *   `current_time`: Текущее время.
    *   *Логика*: Уменьшает счетчик предметов, обновляет время последнего использования.

#### Класс `SlotManager`
Управляет коллекцией слотов (5 и 6).

*   **`__init__(self, regions: Dict[str, Region], delays: Dict[int, float])`**
    *   Инициализирует слоты на основе регионов и задержек.

*   **`set_delay(self, slot: int, delay: float) -> None`**
    *   Обновляет задержку для слота.

*   **`set_active(self, slot: int, active: bool) -> None`**
    *   Активирует/деактивирует слот.

*   **`update_items(self, slot: int, items: int) -> None`**
    *   Обновляет количество предметов в слоте (по данным OCR).

*   **`use_item(self) -> bool`**
    *   Пытается использовать предмет из доступных слотов (5 или 6). Учитывает глобальный кулдаун.

---

## Модуль `src/capture`

### Файл `src/capture/screen.py`

#### Класс `ScreenCapture`
Отвечает за работу с экраном (MSS) и мышью.

*   **`__init__(self)`**
    *   Инициализирует `mss`.

*   **`async capture_region(self, region: Region) -> Optional[np.ndarray]`**
    *   Захватывает область экрана по координатам.
    *   *Возвращает*: Изображение в формате OpenCV (BGR) или None.

*   **`async select_region(self, region_type: str) -> Optional[Region]`**
    *   Интерактивный выбор региона пользователем (два клика мышью).
    *   *Логика*: Запускает слушатель мыши, ждет два клика, вычисляет координаты прямоугольника.

---

## Модуль `src/config`

### Файл `src/config/models.py`

#### Класс `Region` (dataclass)
Описывает прямоугольную область экрана.
*   Поля: `left`, `top`, `width`, `height`.
*   **`validate(self) -> bool`**: Проверяет корректность координат.

#### Класс `Settings` (dataclass)
Хранит настройки логики приложения.
*   Поля: `hp_threshold` (порог лечения), интервалы проверок (`stable`, `healing`, `idle`), `slot_delays`.
*   **`validate(self) -> bool`**: Проверяет диапазоны значений.

#### Класс `Config` (dataclass)
Корневой объект конфигурации.
*   Поля: `settings`, `regions`, `base_path`.

### Файл `src/config/manager.py`

#### Класс `ConfigManager`
Отвечает за загрузку и сохранение конфигурации (JSON).

*   **`__init__(self, base_path: Path)`**
    *   Определяет пути к файлам настроек.

*   **`load_config(self) -> Config`**
    *   Загружает настройки и регионы, возвращает объект `Config`.

*   **`load_settings(self) -> Settings`**
    *   Читает `settings.json`. Если файла нет или он поврежден — возвращает дефолтные настройки.

*   **`load_regions(self) -> Dict[str, Region]`**
    *   Читает `regions.json`. Конвертирует относительные координаты в абсолютные (используя `mss`).

*   **`save_config(self, config: Config) -> None`**
    *   Сохраняет и настройки, и регионы.

*   **`save_settings(self, settings: Settings) -> None`**
    *   Записывает настройки в файл.

*   **`save_regions(self, regions: Dict[str, Region]) -> None`**
    *   Записывает регионы в файл, конвертируя абсолютные координаты в относительные (для поддержки разных разрешений).

---

## Модуль `src/ocr`

### Файл `src/ocr/engine.py`

#### Класс `OCREngine`
Обертка над PaddleOCR.

*   **`__init__(self, debug: bool = False)`**
    *   Инициализирует модель PaddleOCR и препроцессор.

*   **`async process(self, img: np.ndarray, is_slot: bool, region_name: str) -> Optional[int]`**
    *   Основной метод распознавания.
    *   Логика: предобработка изображения -> OCR -> парсинг текста (числа). Делает несколько попыток при неудаче.

*   **`async update_hp(self, img: np.ndarray) -> Optional[int]`**
    *   Распознает значение HP. Кэширует результат.

*   **`async update_slot(self, slot: int, img: np.ndarray) -> int`**
    *   Распознает количество предметов в слоте. Использует кэширование (обновление раз в `update_interval`).

### Файл `src/ocr/preprocessor.py`

#### Класс `Preprocessor`
Подготовка изображения для лучшего распознавания.

*   **`process(self, img: np.ndarray, region_name: str = "Unknown") -> np.ndarray`**
    *   Преобразования:
        1. Оттенки серого (Gray).
        2. Повышение резкости (Sharpen).
        3. Контраст.
        4. Увеличение (Resize x2.5).

---

## Модуль `src/gui`

### Файл `src/gui/main_window.py`

#### Класс `MainWindow`
Главное окно приложения.

*   **`__init__(self, config: Config)`**
    *   Инициализация `AutomationCore`, UI элементов.

*   **`setup_ui(self)`**
    *   Создает кнопки (Start/Stop, Settings, Select Region) и чекбоксы.

*   **`toggle_script(self)`**
    *   Запускает или останавливает `core`. Проверяет наличие регионов.

*   **`start_async_loop(self)`**
    *   Запускает асинхронный цикл обработки `core.run()`.

*   **`select_hp_region(self)` / `select_slot_region(self, slot)`**
    *   Вызывает `core.capture.select_region` и сохраняет результат в конфиг.

### Файл `src/gui/settings_window.py`

#### Класс `SettingsWindow`
Окно настроек.

*   **`apply_settings(self)`**
    *   Считывает значения из полей, валидирует их, обновляет `config` и передает в `core`.

---

## Модуль `src/utils`

### Файл `src/utils/platform.py`

#### Класс `WindowChecker`
*   **`is_app_active(self, app_name: str = "Rust") -> bool`**
    *   Проверяет, активно ли окно приложения (только macOS, использует `AppKit`).

### Файл `src/utils/logging.py`
*   **`setup_logging(base_path: Path)`**
    *   Настраивает `loguru`: вывод в файл и консоль.

---

## Точка входа `src/main.py`
*   Настраивает логирование.
*   Загружает конфигурацию.
*   Запускает `MainWindow`.
