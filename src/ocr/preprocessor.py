import cv2
import numpy as np
from loguru import logger


class Preprocessor:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def process(self, img: np.ndarray, region_name: str = "Unknown") -> np.ndarray:
        logger.debug(f"Preprocessing {region_name}")
        try:
            # 1. Gray
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.debug:
                cv2.imshow(f"{region_name} - Gray", gray)

            # 2. Sharpen
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharp = gray - 0.5 * laplacian
            sharp = np.clip(sharp, 0, 255).astype(np.uint8)
            if self.debug:
                cv2.imshow(f"{region_name} - Sharp", sharp)

            # 3. Contrast
            sharp = cv2.convertScaleAbs(sharp, alpha=1.1, beta=0)
            if self.debug:
                cv2.imshow(f"{region_name} - Contrast", sharp)

            # 4. Resize
            processed = cv2.resize(sharp, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            if self.debug:
                cv2.imshow(f"{region_name} - Resized", processed)
                cv2.waitKey(1)

            return processed
        except Exception as e:
            logger.error(f"Preprocessing failed for {region_name}: {e}")
            return img