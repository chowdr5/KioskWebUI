#!/bin/bash
set -e
if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo ./install.sh"
  exit 1
fi

# Target install directory
TARGET_DIR="/opt/webUI/KioskWebUI/wifi-setup"

# Create nwadmin user if missing
if ! id -u nwadmin >/dev/null 2>&1; then
  useradd -m -s /bin/bash nwadmin
  echo "Created user nwadmin"
fi

# Determine script and project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# Copy project to target if not already there
if [ "$PROJECT_ROOT" != "$TARGET_DIR" ]; then
  echo "Copying project to $TARGET_DIR"
  mkdir -p "$(dirname "$TARGET_DIR")"
  # use rsync if available for a clean copy, fallback to cp
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$PROJECT_ROOT/" "$TARGET_DIR/"
  else
    rm -rf "$TARGET_DIR"
    cp -a "$PROJECT_ROOT" "$TARGET_DIR"
  fi
fi

# Work from the installed target python folder
cd "$TARGET_DIR/python"

# Create venv and install requirements
python3 -m venv venv
. venv/bin/activate
# Ensure pip/setuptools/wheel are recent so modern packages can be installed
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Copy service and sudoers (from target dir)
cp wifi-setup.service /etc/systemd/system/
# Install hotspot service and helper
if [ -f setup-hotspot.service ]; then
  cp setup-hotspot.service /etc/systemd/system/
fi

# Ensure hotspot helper is executable
if [ -f hotspot.sh ]; then
  chmod +x hotspot.sh
fi
mkdir -p /etc/sudoers.d
cp sudoers/wifi-setup-python.sudoers /etc/sudoers.d/wifi-setup-python
chmod 440 /etc/sudoers.d/wifi-setup-python
chmod -R 777 "$TARGET_DIR" 
# Ensure project is owned by nwadmin
chown -R nwadmin:nwadmin "$TARGET_DIR" || true
chmod -R 777 "$TARGET_DIR" || true

systemctl daemon-reload
systemctl enable --now wifi-setup.service
if systemctl list-unit-files | grep -q setup-hotspot.service; then
  systemctl enable --now setup-hotspot.service || true
fi

echo "Installed Python WiFi setup service. Edit /etc/sudoers.d/wifi-setup-python to adjust username if needed."