#!/bin/bash
# Helper to start/stop hotspot using nmcli and set static IP 192.168.50.1
set -e
case "$1" in
  start)
    nmcli device wifi hotspot ifname wlan0 ssid "SetupAP" band bg password "setup1234"
    ip addr add 192.168.50.1/24 dev wlan0 || true
    echo "Hotspot started"
    ;;
  stop)
    nmcli connection down setup-hotspot || true
    echo "Hotspot stopped"
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac
