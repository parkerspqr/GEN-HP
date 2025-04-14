from AppKit import NSWorkspace
from loguru import logger


class WindowChecker:
    def is_app_active(self, app_name: str = "Rust") -> bool:
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            return active_app and active_app["NSApplicationName"] == app_name
        except Exception as e:
            logger.error(f"Failed to check active window: {e}")
            return False