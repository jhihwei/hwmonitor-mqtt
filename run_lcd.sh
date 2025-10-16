#!/bin/bash
# LCD Monitor Launcher for 480x320 TFT Display
# Optimized for terminal devices with small screens

# Set terminal size for LCD (approximate for 480x320)
export COLUMNS=60
export LINES=20

# Run the LCD-optimized viewer
uv run python tui_viewer_lcd.py
