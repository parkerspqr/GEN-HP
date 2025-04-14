from pathlib import Path
from loguru import logger
from src.config.manager import ConfigManager
from src.utils.logging import setup_logging
from src.gui.main_window import MainWindow


def main():
    base_path = Path(__file__).parent.parent
    setup_logging(base_path)
    config_manager = ConfigManager(base_path)
    config = config_manager.load_config()
    config_manager.save_config(config)  # Ensure defaults are saved
    app = MainWindow(config)
    app.run()


if __name__ == "__main__":
    main()