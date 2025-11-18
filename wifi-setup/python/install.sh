#!/bin/bash
set -e
if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo ./install.sh"
  exit 1
fi

# Create nwadmin user if missing
if ! id -u nwadmin >/dev/null 2>&1; then
  useradd -m -s /bin/bash nwadmin
  echo "Created user nwadmin"
fi

# Create venv and install requirements
cd python
python3 -m venv venv
. venv/bin/activate
# Ensure pip/setuptools/wheel are recent so modern packages can be installed
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Copy service and sudoers
cp wifi-setup.service /etc/systemd/system/
mkdir -p /etc/sudoers.d
cp sudoers/wifi-setup-python.sudoers /etc/sudoers.d/wifi-setup-python
chmod 440 /etc/sudoers.d/wifi-setup-python

chown -R nwadmin:nwadmin /home/nwadmin/wifi-setup || true

systemctl daemon-reload
systemctl enable --now wifi-setup.service

echo "Installed Python WiFi setup service. Edit /etc/sudoers.d/wifi-setup-python to adjust username if needed."