#!/bin/bash
set -e

SCRIPT_NAME="ps5-idle-timeout"
INSTALL_DIR="$HOME/.local/share/$SCRIPT_NAME"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
CONFIG_DIR="$HOME/.config/$SCRIPT_NAME"
CONFIG_PATH="$CONFIG_DIR/config.ini"
SERVICE_NAME="$SCRIPT_NAME.service"
SERVICE_PATH="$HOME/.config/systemd/user/$SERVICE_NAME"

echo " Uninstalling $SCRIPT_NAME..."

# Stop and disable systemd service if it exists
if [ -f "$SERVICE_PATH" ]; then
  echo " Stopping systemd user service..."
  systemctl --user stop "$SERVICE_NAME" || true
  systemctl --user disable "$SERVICE_NAME" || true
  rm -f "$SERVICE_PATH"
  systemctl --user daemon-reexec
  echo " Systemd service removed."
fi

# Remove installed script
if [ -f "$BIN_PATH" ]; then
  echo "  Removing CLI tool from ~/.local/bin..."
  rm -f "$BIN_PATH"
fi

# Remove monitor module
if [ -d "$INSTALL_DIR" ]; then
  echo "  Removing installed monitor module..."
  rm -rf "$INSTALL_DIR"
fi

# Optionally remove config
if [ -f "$CONFIG_PATH" ]; then
  read -r -p "  Remove user config at $CONFIG_PATH? [y/N] " CONFIRM
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    rm -f "$CONFIG_PATH"
    echo " Config removed."
  else
    echo "  Skipped config removal."
  fi
fi

echo " $SCRIPT_NAME fully uninstalled."
