#!/bin/bash
# Install script to set up the wifi-setup service and sudoers entry.
set -e

PROJECT_DIR="/home/pi/wifi-setup"
SUDOERS_FILE="/etc/sudoers.d/wifi-setup"
SERVICE_FILE="/etc/systemd/system/wifi-setup.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo ./install.sh"
  exit 1
fi

# Copy service file (assumes current dir is project root)
cp wifi-setup.service $SERVICE_FILE
chmod 644 $SERVICE_FILE

# Copy sudoers file
mkdir -p /etc/sudoers.d
cp sudoers/wifi-setup.sudoers $SUDOERS_FILE
chmod 440 $SUDOERS_FILE

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable --now wifi-setup.service

echo "Install complete. Service enabled. Edit /etc/sudoers.d/wifi-setup to adjust username if needed."