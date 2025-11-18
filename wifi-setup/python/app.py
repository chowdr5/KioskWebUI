from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change-me')

def scan_networks():
    try:
        proc = subprocess.run(['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'device', 'wifi', 'list'], capture_output=True, text=True, check=True)
        lines = proc.stdout.strip().splitlines()
        networks = []
        seen = set()
        for line in lines:
            if not line:
                continue
            parts = line.split(':')
            ssid = parts[0]
            if ssid in seen or ssid == '':
                continue
            seen.add(ssid)
            signal = parts[-1] if len(parts) >= 2 else ''
            security = parts[-2] if len(parts) >= 3 else ''
            networks.append({'ssid': ssid, 'security': security, 'signal': signal})
        return networks
    except Exception:
        return []

@app.route('/')
def index():
    nets = scan_networks()
    return render_template('index.html', networks=nets)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form.get('ssid')
    psk = request.form.get('psk')
    if not ssid:
        flash('SSID required', 'danger')
        return redirect(url_for('index'))
    try:
        if psk:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', psk]
        else:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        flash('Connection started', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Connection failed: {e.stderr or e.stdout}', 'danger')
    return redirect(url_for('index'))

@app.route('/hotspot', methods=['POST'])
def hotspot():
    ssid = request.form.get('hot_ssid')
    psk = request.form.get('hot_psk')
    if not ssid:
        flash('Hotspot SSID required', 'danger')
        return redirect(url_for('index'))
    try:
        # create hotspot via nmcli
        cmd = ['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ifname', 'wlan0', 'con-name', 'setup-hotspot', 'ssid', ssid]
        if psk:
            cmd += ['password', psk]
        subprocess.run(cmd, check=True)
        # set static IP (example)
        subprocess.run(['sudo', 'ip', 'addr', 'add', '192.168.50.1/24', 'dev', 'wlan0'], check=False)
        flash('Hotspot started on 192.168.50.1', 'success')
    except Exception as e:
        flash(f'Failed to start hotspot: {e}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
