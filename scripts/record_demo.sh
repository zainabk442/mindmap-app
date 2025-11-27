#!/usr/bin/env bash
# Script example to record the app window using ffmpeg on Windows (PowerShell example).
# Replace <WINDOW_TITLE> with "TUBA KHAN — AIR MINDMAP" or use screen capture.

# Example command for PowerShell:
# ffmpeg -f gdigrab -framerate 30 -i title="TUBA KHAN — AIR MINDMAP" -pix_fmt yuv420p -r 30 output/demo_record.mp4

echo "Use the following ffmpeg command in PowerShell to record the app window:"
echo "ffmpeg -f gdigrab -framerate 30 -i title=\"TUBA KHAN — AIR MINDMAP\" -pix_fmt yuv420p -r 30 output/demo_record.mp4"
