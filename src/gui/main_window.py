import tkinter as tk
import asyncio
from tkinter import messagebox
from pathlib import Path
from loguru import logger
from ..config.models import Config
from ..config.manager import ConfigManager
from ..automation.core import AutomationCore
from .settings_window import SettingsWindow


class MainWindow:
    def __init__(self, config: Config):
        self.config = config
        self.core = AutomationCore(config, debug=True)
        self.is_running = False
        self.root = tk.Tk()
        self.root.title("AutoHPrust")
        self.root.geometry("400x300")
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.loop = asyncio.get_event_loop()
        logger.info("MainWindow initialized")

    def setup_ui(self):
        self.status_label = tk.Label(self.root, text="Status: Stopped")
        self.status_label.pack(pady=10)

        self.start_stop_btn = tk.Button(
            self.root, text="Start", command=self.toggle_script
        )
        self.start_stop_btn.pack(pady=5)

        tk.Button(self.root, text="Settings", command=self.open_settings).pack(
            pady=5
        )

        tk.Label(self.root, text="Regions:").pack(pady=5)
        tk.Button(
            self.root, text="Select HP Region", command=self.select_hp_region
        ).pack(pady=2)
        tk.Button(
            self.root, text="Select Slot 5 Region", command=lambda: self.select_slot_region(5)
        ).pack(pady=2)
        tk.Button(
            self.root, text="Select Slot 6 Region", command=lambda: self.select_slot_region(6)
        ).pack(pady=2)

        self.slot_5_var = tk.BooleanVar(value=True)
        self.slot_6_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.root,
            text="Slot 5 Active",
            variable=self.slot_5_var,
            command=self.toggle_slot_5,
        ).pack(pady=2)
        tk.Checkbutton(
            self.root,
            text="Slot 6 Active",
            variable=self.slot_6_var,
            command=self.toggle_slot_6,
        ).pack(pady=2)

    def toggle_script(self):
        if not all(
            key in self.config.regions for key in ["hp", "slot_5", "slot_6"]
        ):
            messagebox.showerror(
                "Error", "Please select all regions before starting"
            )
            self.status_label.config(text="Error: Select all regions")
            logger.error("Attempted to start without all regions selected")
            return

        if self.is_running:
            self.core.stop()
            self.is_running = False
            self.start_stop_btn.config(text="Start")
            self.status_label.config(text="Status: Stopped")
            logger.info("Script stopped")
        else:
            self.is_running = True
            self.start_stop_btn.config(text="Stop")
            self.status_label.config(text="Status: Running")
            logger.info("Script started")
            self.root.after(100, self.start_async_loop)

    def start_async_loop(self):
        if self.is_running:
            try:
                self.loop.run_until_complete(self.run_core())
            except Exception as e:
                logger.error(f"Async loop failed: {e}", exc_info=True)
                self.is_running = False
                self.start_stop_btn.config(text="Start")
                self.status_label.config(text="Status: Error")
                messagebox.showerror("Error", f"Script failed: {e}")

    async def run_core(self):
        logger.debug("Starting core.run")
        await self.core.run()
        logger.debug("Core.run finished")
        self.is_running = False
        self.start_stop_btn.config(text="Start")
        self.status_label.config(text="Status: Stopped")

    def select_hp_region(self):
        region = self.loop.run_until_complete(self.core.capture.select_region("HP"))
        if region:
            self.config.regions["hp"] = region
            ConfigManager(self.config.base_path).save_config(self.config)
            logger.info("HP region selected")

    def select_slot_region(self, slot: int):
        region = self.loop.run_until_complete(
            self.core.capture.select_region(f"Slot {slot}")
        )
        if region:
            self.config.regions[f"slot_{slot}"] = region
            ConfigManager(self.config.base_path).save_config(self.config)
            logger.info(f"Slot {slot} region selected")

    def toggle_slot_5(self):
        self.core.set_slot_active(5, self.slot_5_var.get())
        logger.debug(f"Slot 5 active: {self.slot_5_var.get()}")

    def toggle_slot_6(self):
        self.core.set_slot_active(6, self.slot_6_var.get())
        logger.debug(f"Slot 6 active: {self.slot_6_var.get()}")

    def open_settings(self):
        SettingsWindow(self.root, self.config, self.on_settings_updated)
        logger.debug("Settings window opened")

    def on_settings_updated(self, config: Config):
        self.loop.run_until_complete(self.core.update_config(config))
        self.config = config
        logger.info("Settings updated")

    def on_closing(self):
        if self.is_running:
            self.core.stop()
        self.root.destroy()
        logger.info("Application closed")

    def run(self):
        self.root.mainloop()