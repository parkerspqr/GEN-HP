import tkinter as tk
from typing import Optional
from loguru import logger
from ..config.models import Config, Settings
from ..automation.core import AutomationCore


class SettingsWindow:
    def __init__(self, parent: tk.Tk, config: Config, core: AutomationCore):
        self.config = config
        self.core = core
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("300x350")
        self.setup_ui()

    def setup_ui(self) -> None:
        tk.Label(self.window, text="Check Intervals (sec):").pack(pady=5)

        tk.Label(self.window, text=f"HP Threshold (current: {self.config.settings.hp_threshold}):").pack()
        self.hp_entry = tk.Entry(self.window)
        self.hp_entry.insert(0, str(self.config.settings.hp_threshold))
        self.hp_entry.pack()

        tk.Label(
            self.window, text=f"Stable HP (current: {self.config.settings.check_interval_stable}):"
        ).pack()
        self.stable_entry = tk.Entry(self.window)
        self.stable_entry.insert(0, str(self.config.settings.check_interval_stable))
        self.stable_entry.pack()

        tk.Label(
            self.window, text=f"Healing (current: {self.config.settings.check_interval_healing}):"
        ).pack()
        self.healing_entry = tk.Entry(self.window)
        self.healing_entry.insert(0, str(self.config.settings.check_interval_healing))
        self.healing_entry.pack()

        tk.Label(self.window, text=f"HP Fall (current: {self.config.settings.check_interval_idle}):").pack()
        self.fall_entry = tk.Entry(self.window)
        self.fall_entry.insert(0, str(self.config.settings.check_interval_idle))
        self.fall_entry.pack()

        tk.Label(
            self.window, text=f"Slot 5 Delay (current: {self.config.settings.slot_delays[5]}):"
        ).pack()
        self.slot_5_delay_entry = tk.Entry(self.window)
        self.slot_5_delay_entry.insert(0, str(self.config.settings.slot_delays[5]))
        self.slot_5_delay_entry.pack()

        tk.Label(
            self.window, text=f"Slot 6 Delay (current: {self.config.settings.slot_delays[6]}):"
        ).pack()
        self.slot_6_delay_entry = tk.Entry(self.window)
        self.slot_6_delay_entry.insert(0, str(self.config.settings.slot_delays[6]))
        self.slot_6_delay_entry.pack()

        tk.Button(self.window, text="Apply", command=self.apply_settings).pack(pady=10)

        self.error_label = tk.Label(self.window, text="", fg="red")
        self.error_label.pack()

    def apply_settings(self) -> None:
        try:
            hp_threshold = float(self.hp_entry.get())
            stable = float(self.stable_entry.get())
            healing = float(self.healing_entry.get())
            fall = float(self.fall_entry.get())
            slot_5_delay = float(self.slot_5_delay_entry.get())
            slot_6_delay = float(self.slot_6_delay_entry.get())

            if not (0 <= hp_threshold <= 150):
                self.error_label.config(text="HP must be 0-150")
                return
            if not all(x > 0 for x in [stable, healing, fall, slot_5_delay, slot_6_delay]):
                self.error_label.config(text="Values must be positive")
                return

            new_settings = Settings(
                hp_threshold=hp_threshold,
                check_interval_stable=stable,
                check_interval_healing=healing,
                check_interval_idle=fall,
                slot_delays={5: slot_5_delay, 6: slot_6_delay},
            )
            self.config.settings = new_settings
            import asyncio

            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.core.update_config(self.config))
            self.window.destroy()
        except ValueError:
            self.error_label.config(text="Enter valid numbers")