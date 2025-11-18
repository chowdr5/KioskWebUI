WiFi Setup Web UI

This small Flask app lets you configure Wi-Fi on a Raspberry Pi by writing a wpa_supplicant configuration.

Files:
- `app.py` - Flask app that serves the web UI and writes `/etc/wpa_supplicant/wpa_supplicant.conf` (requires sudo).
- `templates/index.html` - Simple form to enter SSID and password.
- `requirements.txt` - Python dependencies.

Install and enable (on Raspberry Pi):

1. Create a Python virtualenv and install dependencies:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

2. Run the app (for testing):

```bash
sudo python3 app.py
```

3. To run as a service, create and enable a systemd unit (an example `wifi-setup.service` is included in this project). Then use `sudo systemctl enable --now wifi-setup.service`.

Security notes:
- The web UI writes system Wi-Fi config; restrict access or run on a private network/initial access point.
- Change `FLASK_SECRET` environment variable to a strong secret.
