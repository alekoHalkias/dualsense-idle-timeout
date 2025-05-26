#!/bin/bash
set -e

SCRIPT_NAME="ps5-idle-timeout"
SCRIPT_SOURCE="./ps5-idle-timeout.py"
MODULE_DIR="./monitor"
INSTALL_DIR="$HOME/.local/share/$SCRIPT_NAME"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
SERVICE_SOURCE="./ps5-idle-timeout.service"
SERVICE_DEST="$HOME/.config/systemd/user/$SCRIPT_NAME.service"

echo "Installing $SCRIPT_NAME..."

# Ensure destination directories exist
mkdir -p "$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.config/systemd/user"

# Copy monitor module to shared location
cp -r "$MODULE_DIR" "$INSTALL_DIR/"

# Inject runtime PYTHONPATH logic into the script copy
echo '#!/usr/bin/env python3' > "$BIN_PATH"
echo "import sys; sys.path.insert(0, '$INSTALL_DIR')" >> "$BIN_PATH"
tail -n +2 "$SCRIPT_SOURCE" >> "$BIN_PATH"
chmod +x "$BIN_PATH"

# Copy and enable the systemd user service
install -Dm644 "$SERVICE_SOURCE" "$SERVICE_DEST"
systemctl --user daemon-reexec
systemctl --user daemon-reload
systemctl --user enable --now "$SCRIPT_NAME.service"

echo "$SCRIPT_NAME Done!"
