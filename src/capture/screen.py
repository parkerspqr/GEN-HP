import asyncio
import numpy as np
import mss
import cv2
from pynput import mouse
from typing import Optional
from loguru import logger
from ..config.models import Region


class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    async def capture_region(self, region: Region) -> Optional[np.ndarray]:
        try:
            screenshot = self.sct.grab(
                {
                    "left": region.left,
                    "top": region.top,
                    "width": region.width,
                    "height": region.height,
                }
            )
            img = np.array(screenshot)
            if np.any(img):
                return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            logger.warning("Captured image is black")
            return None
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None

    async def select_region(self, region_type: str) -> Optional[Region]:
        points = []
        def on_click(x, y, button, pressed):
            if button == mouse.Button.left and pressed:
                points.append((x, y))
                logger.info(f"Point {len(points)}: ({x}, {y})")
                if len(points) == 2:
                    return False

        logger.info(f"Select region for {region_type}: click twice")
        listener = mouse.Listener(on_click=on_click)
        listener.start()
        while len(points) < 2:
            await asyncio.sleep(0.1)
        listener.stop()

        if len(points) != 2:
            logger.error("Region selection cancelled")
            return None

        start_x, start_y = points[0]
        end_x, end_y = points[1]
        region = Region(
            left=min(start_x, end_x),
            top=min(start_y, end_y),
            width=abs(start_x - end_x),
            height=abs(start_y - end_y),
        )
        logger.info(f"Region selected for {region_type}: {region}")
        return region