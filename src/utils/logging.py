from loguru import logger
from pathlib import Path


def setup_logging(base_path: Path):
    logger.remove()
    log_file = base_path / "logs" / "autohprust.log"
    log_file.parent.mkdir(exist_ok=True)
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )