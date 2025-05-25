#!/bin/bash
set -e

SCRIPT_NAME="ps5-idle-timeout"
SCRIPT_SOURCE="./ps5-idle-timeout.py"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
SERVICE_SOURCE="./ps5-idle-timeout.service"
SERVICE_DEST="$HOME/.config/systemd/user/$SCRIPT_NAME.service"

echo "Installing $SCRIPT_NAME..."

# Copy script to ~/.local/bin and make it executable
cp "$SCRIPT_SOURCE" "$BIN_PATH"
chmod +x "$BIN_PATH"

# Copy systemd service file
cp "$SERVICE_SOURCE" "$SERVICE_DEST"

# Reload systemd and enable service
systemctl --user daemon-reexec
systemctl --user daemon-reload
systemctl --user enable --now "$SCRIPT_NAME.service"

echo "Done!"