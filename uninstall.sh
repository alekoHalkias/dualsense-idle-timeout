#!/bin/bash
set -e

SCRIPT_NAME="ps5-idle-timeout"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
INSTALL_DIR="$HOME/.local/share/$SCRIPT_NAME"
# SERVICE_DEST="$HOME/.config/systemd/user/$SCRIPT_NAME.service"
CONFIG_DIR="$HOME/.config/$SCRIPT_NAME"

echo "🗑️ Uninstalling $SCRIPT_NAME..."

# Stop and disable the systemd service
# systemctl --user disable --now "$SCRIPT_NAME.service" || true

# Remove installed files
rm -f "$BIN_PATH"
rm -rf "$INSTALL_DIR"
# rm -f "$SERVICE_DEST"
rm -rf "$CONFIG_DIR"

# # Reload systemd user daemon
# systemctl --user daemon-reexec
# systemctl --user daemon-reload

echo "$SCRIPT_NAME removed."
