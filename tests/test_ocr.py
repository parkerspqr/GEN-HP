import pytest
import asyncio
import numpy as np
from unittest.mock import patch
from src.ocr.engine import OCREngine
from src.config.models import Config, Settings, Region
from pathlib import Path
import time


@pytest.fixture
def config():
    base_path = Path(__file__).parent.parent
    return Config(
        settings=Settings(),
        regions={
            "hp": Region(
                left=100,
                top=100,
                width=50,
                height=20,
            ),
            "slot_5": Region(
                left=200,
                top=300,
                width=50,
                height=20,
            ),
            "slot_6": Region(
                left=260,
                top=300,
                width=50,
                height=20,
            ),
        },
        base_path=Path(base_path),
    )


@pytest.fixture
def ocr(config):
    return OCREngine(debug=False)


def test_empty_slot(ocr):
    """Test OCR handling of empty slot (no text)."""
    img = np.zeros((20, 50, 3), dtype=np.uint8)  # Simulate empty slot
    result = asyncio.run(ocr.update_slot(5, img))
    assert result == 0, f"Expected 0 for empty slot, got {result}"


def test_slot_with_items(ocr):
    """Test OCR handling of slot with items (e.g., x33)."""
    # Simulate PaddleOCR output for text "x33"
    with patch.object(
        ocr.reader,
        "ocr",
        return_value=[[([[0, 0], [10, 0], [10, 10], [0, 10]], ("x33", 0.9))]],
    ):
        img = np.ones((20, 50, 3), dtype=np.uint8) * 255  # Simulate white image
        result = asyncio.run(ocr.update_slot(5, img))
        assert result == 33, f"Expected 33 for slot with x33, got {result}"


def test_slot_cache(ocr):
    """Test slot cache behavior within 2 seconds."""
    ocr.slot_caches[5] = 10
    ocr.slot_last_update[5] = time.time() - 1.0
    img = np.ones((20, 50, 3), dtype=np.uint8) * 255
    result = asyncio.run(ocr.update_slot(5, img))
    assert result == 10, f"Expected cached value 10, got {result}"


def test_slot_retries(ocr):
    """Test retries for unrecognized slot."""
    with patch.object(ocr.reader, "ocr", return_value=None):
        img = np.ones((20, 50, 3), dtype=np.uint8) * 255
        result = asyncio.run(ocr.update_slot(5, img))
        assert result == 0, f"Expected 0 after retries, got {result}"


def test_hp_recognition(ocr):
    """Test HP recognition."""
    # Simulate PaddleOCR output for text "90"
    with patch.object(
        ocr.reader,
        "ocr",
        return_value=[[([[0, 0], [10, 0], [10, 10], [0, 10]], ("90", 0.9))]],
    ):
        img = np.ones((20, 50, 3), dtype=np.uint8) * 255
        result = asyncio.run(ocr.update_hp(img))
        assert result == 90, f"Expected HP 90, got {result}"


def test_invalid_hp(ocr):
    """Test handling of invalid HP."""
    with patch.object(
        ocr.reader,
        "ocr",
        return_value=[[([[0, 0], [10, 0], [10, 10], [0, 10]], ("abc", 0.9))]],
    ):
        img = np.ones((20, 50, 3), dtype=np.uint8) * 255
        result = asyncio.run(ocr.update_hp(img))
        assert result is None, f"Expected None for invalid HP, got {result}"


if __name__ == "__main__":
    pytest.main([__file__])