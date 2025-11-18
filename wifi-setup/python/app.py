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


def _remove_conflicting_connection(ssid: str):
    """Remove any existing NetworkManager connection whose SSID or NAME
    matches the requested SSID and is a wifi connection. We check both the
    connection NAME and the configured 802-11-wireless.ssid property to catch
    stale profiles that would otherwise be reused.
    """
    try:
        proc = subprocess.run(['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'], capture_output=True, text=True, check=True)
        for line in proc.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            name, ctype = parts[0], parts[1]
            if ctype != '802-11-wireless':
                continue
            # Try to read the configured SSID for this connection. If the
            # property isn't present or the command fails, treat it as empty.
            try:
                ssid_proc = subprocess.run(['sudo', 'nmcli', '-g', '802-11-wireless.ssid', 'connection', 'show', name], capture_output=True, text=True, check=True)
                cfg_ssid = ssid_proc.stdout.strip()
            except subprocess.CalledProcessError:
                cfg_ssid = ''
            # If either the connection name or its configured SSID matches,
            # delete the profile so nmcli will create a fresh one.
            if name == ssid or cfg_ssid == ssid:
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', name], check=False)
    except Exception:
        # best-effort only; don't prevent UI flow on errors here
        pass

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
        # Remove any existing connection profile that matches this SSID so
        # NetworkManager won't try to reuse a stale profile.
        _remove_conflicting_connection(ssid)

        # Create a temporary connection name to avoid collisions
        import time
        temp_name = f"wifi-setup-{int(time.time())}"

        # First try the higher-level command which both creates a profile and
        # brings it up in one step. We add a profile name so it doesn't reuse
        # an existing one.
        try:
            if psk:
                connect_cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', psk, 'ifname', 'wlan0', 'con-name', temp_name]
            else:
                connect_cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'ifname', 'wlan0', 'con-name', temp_name]
            proc = subprocess.run(connect_cmd, capture_output=True, text=True, check=True)
            flash('Connection started', 'success')
        except subprocess.CalledProcessError as e:
            # If we get the key-mgmt error or similar, fall back to explicitly
            # creating/modifying a profile and then bringing it up.
            stderr = (e.stderr or e.stdout or '').lower()
            if 'key-mgmt' in stderr or '802-11-wireless-security' in stderr:
                # explicit creation and modification
                subprocess.run(['sudo', 'nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', 'wlan0', 'con-name', temp_name, 'ssid', ssid], check=False)
                if psk:
                    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', temp_name, 'wifi-sec.key-mgmt', 'wpa-psk'], check=False)
                    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', temp_name, 'wifi-sec.psk', psk], check=False)
                subprocess.run(['sudo', 'nmcli', 'connection', 'modify', temp_name, 'connection.autoconnect', 'no'], check=False)
                # try bring up
                proc2 = subprocess.run(['sudo', 'nmcli', 'connection', 'up', temp_name], capture_output=True, text=True, check=False)
                if proc2.returncode == 0:
                    flash('Connection started', 'success')
                else:
                    flash(f'Connection failed: {proc2.stderr or proc2.stdout or stderr}', 'danger')
            else:
                flash(f'Connection failed: {e.stderr or e.stdout}', 'danger')
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
    app.run(host='0.0.0.0', port=8080)
