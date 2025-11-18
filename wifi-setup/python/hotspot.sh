#!/bin/bash
# Helper to start/stop a hotspot using NetworkManager (nmcli).
# Creates (if needed) a connection named 'setup-hotspot' that runs in AP mode,
# sets the IPv4 address to 192.168.50.1/24 (shared) and brings it up.

set -euo pipefail

CON_NAME="setup-hotspot"
IFACE="wlan0"
SSID="SetupAP"
PSK="setup1234"
IPADDR="192.168.50.1/24"

usage() {
  echo "Usage: $0 {start|stop|status}" >&2
  exit 1
}

start_hotspot() {
  # If connection exists, update it; otherwise create it
  if nmcli -g NAME connection show | grep -xq "$CON_NAME"; then
    echo "Updating existing connection $CON_NAME"
  else
    echo "Creating connection $CON_NAME"
    nmcli connection add type wifi ifname "$IFACE" con-name "$CON_NAME" autoconnect no ssid "$SSID"
  fi

  # Configure as AP
  nmcli connection modify "$CON_NAME" 802-11-wireless.mode ap 802-11-wireless.band bg
  nmcli connection modify "$CON_NAME" 802-11-wireless.ssid "$SSID"
  nmcli connection modify "$CON_NAME" wifi-sec.key-mgmt wpa-psk
  nmcli connection modify "$CON_NAME" wifi-sec.psk "$PSK"

  # Set IPv4 to shared and assign address (NetworkManager will provide DHCP/NAT)
  nmcli connection modify "$CON_NAME" ipv4.method shared ipv4.addresses "$IPADDR"
  nmcli connection modify "$CON_NAME" connection.autoconnect no

  # Bring up connection
  nmcli connection up "$CON_NAME"
  echo "Hotspot started (SSID=$SSID) — interface $IFACE should have $IPADDR"
}

stop_hotspot() {
  echo "Bringing down $CON_NAME"
  nmcli connection down "$CON_NAME" || true
}

status_hotspot() {
  nmcli -f NAME,TYPE,DEVICE,STATE connection show --active | grep -E "(^$CON_NAME\s)" || echo "$CON_NAME not active"
}

case "${1:-}" in
  start)
    start_hotspot
    ;;
  stop)
    stop_hotspot
    ;;
  status)
    status_hotspot
    ;;
  *)
    usage
    ;;
esac
