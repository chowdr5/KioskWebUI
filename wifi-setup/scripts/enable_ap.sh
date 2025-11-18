#!/bin/bash
# Optional helper to enable hostapd/dnsmasq for initial AP mode (placeholder)
# User must configure hostapd.conf and dnsmasq.conf appropriately.

set -e
sudo systemctl stop wpa_supplicant.service || true
sudo systemctl start hostapd
sudo systemctl start dnsmasq

echo "AP mode started. Configure hostapd/dnsmasq as needed."