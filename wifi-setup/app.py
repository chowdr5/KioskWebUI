from flask import Flask, render_template, request, redirect, url_for, flash
import os
import subprocess

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change-me')

# Path placeholder (NetworkManager handles connections, files live under /run/NetworkManager/system-connections)

def scan_networks():
    """Use nmcli to list available Wi-Fi networks and return a list of dicts.
    Each dict contains: ssid, security, signal
    """
    try:
        # Use terse output with fields SSID,SECURITY,SIGNAL separated by ':'
        proc = subprocess.run(['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'device', 'wifi', 'list'],
                               capture_output=True, text=True, check=True)
        lines = proc.stdout.strip().splitlines()
        networks = []
        seen = set()
        for line in lines:
            if not line:
                continue
            parts = line.split(':')
            # parts[0]=SSID, parts[-1]=SIGNAL, parts[-2]=SECURITY (if present)
            ssid = parts[0]
            if ssid in seen or ssid == '':
                continue
            seen.add(ssid)
            signal = parts[-1] if len(parts) >= 2 else ''
            security = parts[-2] if len(parts) >= 3 else ''
            networks.append({'ssid': ssid, 'security': security, 'signal': signal})
        return networks
    except subprocess.CalledProcessError as e:
        # nmcli failed (maybe not installed); return empty list
        return []
    except Exception:
        return []

@app.route('/')
def index():
    networks = scan_networks()
    return render_template('index.html', networks=networks)

@app.route('/configure', methods=['POST'])
def configure():
    ssid = request.form.get('ssid')
    psk = request.form.get('psk')
    if not ssid:
        flash('SSID is required', 'danger')
        return redirect(url_for('index'))

    # Use nmcli to connect (NetworkManager will create a connection profile)
    try:
        if psk:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', psk]
        else:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        flash(f'Attempt to connect to {ssid} succeeded: {proc.stdout}', 'success')
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout
        flash(f'Failed to connect to {ssid}: {err}', 'danger')
    except Exception as e:
        flash(f'Unexpected error while connecting: {e}', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run on port 80 (requires sudo) and listen on all interfaces
    app.run(host='0.0.0.0', port=80, debug=False)
