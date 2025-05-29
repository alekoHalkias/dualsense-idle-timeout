#!/bin/bash
set -e

SCRIPT_NAME="ps5-idle-timeout"
SCRIPT_SOURCE="./ps5-idle-timeout.py"
MODULE_DIR="./monitor"
INSTALL_DIR="$HOME/.local/share/$SCRIPT_NAME"
BIN_PATH="$HOME/.local/bin/$SCRIPT_NAME"
SERVICE_SOURCE="./ps5-idle-timeout.service"
SERVICE_DEST="$HOME/.config/systemd/user/$SCRIPT_NAME.service"
CONFIG_DIR="$HOME/.config/$SCRIPT_NAME"
CONFIG_PATH="$CONFIG_DIR/config.ini"
DEFAULT_CONFIG="./config.ini"

echo " Installing $SCRIPT_NAME..."

# Ensure destination directories exist
mkdir -p "$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$HOME/.config/systemd/user"

# Copy monitor module to shared location
cp -r "$MODULE_DIR" "$INSTALL_DIR/"

# Inject runtime PYTHONPATH logic into the script copy
echo '#!/usr/bin/env python3' > "$BIN_PATH"
echo "import sys; sys.path.insert(0, '$INSTALL_DIR')" >> "$BIN_PATH"
tail -n +2 "$SCRIPT_SOURCE" >> "$BIN_PATH"
chmod +x "$BIN_PATH"

# Copy default config only if one doesn't already exist
if [ ! -f "$CONFIG_PATH" ]; then
  echo " Installing default config to $CONFIG_PATH"
  cp "$DEFAULT_CONFIG" "$CONFIG_PATH"
else
  echo " Config already exists at $CONFIG_PATH, skipping."
fi

read -r -p "  Install and run as a systemd user service? [y/N] " CONFIRM
if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
  # SERVICE_SOURCE="./ps5-idle-timeout.service"
  SERVICE_DEST="$HOME/.config/systemd/user/$SCRIPT_NAME.service"

  # Patch unit to use resolved path
  sed "s|/path/to/project|$INSTALL_DIR|g" "$SERVICE_SOURCE" > "$SERVICE_DEST"

  systemctl --user daemon-reexec
  systemctl --user daemon-reload
  systemctl --user enable --now "$SCRIPT_NAME.service"
  echo " Systemd service enabled."
else
  echo "  Skipped systemd service setup. You can run manually:"
  echo "   $BIN_PATH --daemon"
fi


echo " $SCRIPT_NAME installed and running."
echo " To run manually:"
echo "   $BIN_PATH --status"
echo
echo " Config location:"
echo "   $CONFIG_PATH"

