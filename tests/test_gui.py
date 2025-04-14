import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock
from src.gui.main_window import MainWindow
from src.config.models import Config, Settings, Region
from pathlib import Path


@pytest.fixture
def config():
    base_path = Path(__file__).parent.parent
    return Config(
        settings=Settings(
            hp_threshold=90.0,
            check_interval_stable=0.2,
            check_interval_healing=0.1,
            check_interval_idle=0.1,
            slot_delays={5: 1.0, 6: 1.0},
        ),
        regions={
            "hp": Region(left=100, top=100, width=50, height=20),
            "slot_5": Region(left=200, top=300, width=50, height=20),
            "slot_6": Region(left=260, top=300, width=50, height=20),
        },
        base_path=base_path,
    )


@pytest.fixture
def main_window(config):
    root = tk.Tk()
    window = MainWindow(config)
    window.root = root
    yield window
    root.destroy()


def test_initial_ui(main_window):
    """Test initial UI setup."""
    assert main_window.root.title() == "AutoHPrust"
    assert main_window.status_label["text"] == "Status: Stopped"
    assert main_window.start_stop_btn["text"] == "Start"


def test_toggle_script_with_regions(main_window):
    """Test script toggle with all regions set."""
    with patch.object(main_window.core, "run", return_value=MagicMock()):
        main_window.toggle_script()
        assert main_window.status_label["text"] == "Status: Running"
        assert main_window.start_stop_btn["text"] == "Stop"


def test_toggle_script_without_regions(main_window):
    """Test script toggle without regions."""
    main_window.config.regions = {}
    main_window.toggle_script()
    assert main_window.status_label["text"] == "Error: Select all regions"
    assert main_window.start_stop_btn["text"] == "Start"


def test_slot_active_toggle(main_window):
    """Test toggling slot active state."""
    with patch.object(main_window.core, "set_slot_active") as mock_set:
        main_window.slot_5_var.set(False)
        main_window.toggle_slot_5()
        mock_set.assert_called_with(5, False)


def test_open_settings(main_window):
    """Test opening settings window."""
    with patch("src.gui.settings_window.SettingsWindow") as mock_settings:
        main_window.open_settings()
        mock_settings.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])