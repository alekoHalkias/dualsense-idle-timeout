#!/usr/bin/env bash

set -e

SCRIPT_NAME="ps5-idle-timeout"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
SERVICE_PATH="$HOME/.config/systemd/user/$SCRIPT_NAME.service"

echo "Uninstalling $SCRIPT_NAME..."

# Stop the systemd service if it's running
if systemctl --user is-active --quiet "$SCRIPT_NAME.service"; then
    echo "Stopping service..."
    systemctl --user stop "$SCRIPT_NAME.service"
fi

# Disable the service
if systemctl --user is-enabled --quiet "$SCRIPT_NAME.service"; then
    echo "Disabling service..."
    systemctl --user disable "$SCRIPT_NAME.service"
fi

# Remove systemd service file
if [[ -f "$SERVICE_PATH" ]]; then
    echo "Removing service file..."
    rm -f "$SERVICE_PATH"
fi

# Remove script binary
if [[ -f "$BIN_PATH" ]]; then
    echo "Removing script from ~/.local/bin..."
    rm -f "$BIN_PATH"
fi

# Reload systemd
systemctl --user daemon-reload

echo "Uninstall complete."
