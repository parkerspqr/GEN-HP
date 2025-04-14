# AutoHPrust

A macOS application for automating item usage in Rust based on health (HP) monitoring.

## Features
- Monitors HP and uses items from slots 5/6 when HP falls below a threshold.
- OCR-based detection using PaddleOCR.
- Configurable intervals and delays.
- Tkinter GUI for region selection and settings.
- Debug mode for visual feedback.

## Requirements
- Python 3.10+
- macOS ARM
- Dependencies: see `requirements.txt`

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd autohprust