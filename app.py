import os
import sys
import subprocess
import threading
import time
import requests
from datetime import datetime, timedelta

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from flask_socketio import SocketIO

os.environ['PYTHONUNBUFFERED'] = '1'

app = Flask(__name__)
app.secret_key = "bot_secret_access_key_2026_99"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

user_sessions = {}
ADMIN_CONFIG = "admin_config.txt"

# ================= HTML LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Core | Login</title>
    <style>
        :root {
            --primary: #00f2fe;
            --secondary: #4facfe;
            --accent: #f093fb;
            --bg-dark: #080a0f;
            --glass: rgba(255, 255, 255, 0.05);
        }

        body { 
            background: radial-gradient(circle at center, #1a1a2e 0%, #080a0f 100%);
            display: flex; justify-content: center; align-items: center; 
            height: 100vh; margin: 0; 
            font-family: 'Segoe UI', Tahoma, sans-serif; color: #fff;
            overflow: hidden;
        }

        body::before {
            content: ""; position: absolute; width: 300px; height: 300px;
            background: var(--secondary); filter: blur(150px);
            top: 10%; left: 10%; z-index: -1; opacity: 0.4;
            animation: move 10s infinite alternate;
        }

        @keyframes move {
            from { transform: translate(0, 0); }
            to { transform: translate(100px, 100px); }
        }

        .login-card { 
            background: var(--glass);
            backdrop-filter: blur(20px);
            padding: 40px; border-radius: 24px; width: 360px; 
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            animation: fadeIn 0.8s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .logo-section { text-align: center; margin-bottom: 35px; }
        .logo-icon { 
            font-size: 40px; margin-bottom: 10px;
            filter: drop-shadow(0 0 10px var(--primary));
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .logo-text { 
            letter-spacing: 5px; font-weight: 800; font-size: 24px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        .input-group { margin-bottom: 25px; }
        .label { 
            font-size: 11px; font-weight: 600; text-transform: uppercase; 
            margin-bottom: 8px; display: block; color: rgba(255,255,255,0.6);
        }

        input { 
            width: 100%; padding: 14px 18px; 
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 12px; color: #fff; box-sizing: border-box; 
            transition: all 0.3s;
        }

        input:focus { 
            border-color: var(--primary); outline: none; 
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
        }

        .login-btn { 
            background: linear-gradient(45deg, var(--secondary), var(--accent));
            color: white; border: none; width: 100%; padding: 16px; 
            border-radius: 12px; font-weight: 700; cursor: pointer; 
            transition: 0.3s; text-transform: uppercase; letter-spacing: 2px;
            box-shadow: 0 10px 20px rgba(79, 172, 254, 0.3);
        }

        .login-btn:hover { transform: scale(1.02); filter: brightness(1.1); }

        .info-footer { 
            margin-top: 30px; background: rgba(255,255,255,0.03); 
            padding: 15px; border-radius: 12px; font-size: 11px; 
            text-align: center; color: rgba(255,255,255,0.4); 
        }

        #msg { 
            background: rgba(255, 68, 68, 0.1); color: #ff4444; padding: 10px; 
            border-radius: 8px; font-size: 13px; text-align: center; 
            margin-bottom: 20px; border: 1px solid rgba(255, 68, 68, 0.2);
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo-section">
            <div class="logo-icon">💠</div>
            <div class="logo-text">Login TCP bot</div>
        </div>
        <div id="msg">Invalid credentials!</div>
        <div class="input-group">
            <label class="label">User Identity</label>
            <input type="text" id="u" placeholder="Username">
        </div>
        <div class="input-group">
            <label class="label">Security Key</label>
            <input type="password" id="p" placeholder="••••••••">
        </div>
        <button class="login-btn" onclick="doLogin()">Authorize Access ➜</button>
        <div class="info-footer">
            <span>ⓘ : tk-ngu / mk-sikibidiexe453</span><br>
            Developer @Sikibidiexe | 2008 Edition
        </div>
    </div>
    <script>
        async function doLogin() {
            const u = document.getElementById('u').value;
            const p = document.getElementById('p').value;
            const msg = document.getElementById('msg');
            const resp = await fetch('/api/login_auth', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await resp.json();
            if(data.status === 'success') {
                window.location.href = '/';
            } else {
                msg.style.display = 'block';
                setTimeout(() => { msg.style.display = 'none'; }, 3000);
            }
        }
    </script>
</body>
</html>
"""
# ================= CONFIG =================
def get_config():
    conf = {"pass": "admin123", "duration": 120}
    if os.path.exists(ADMIN_CONFIG):
        with open(ADMIN_CONFIG, 'r') as f:
            for line in f:
                if '=' in line:
                    key, val = line.strip().split('=')
                    if key == 'admin_password': conf['pass'] = val
                    if key == 'global_duration': conf['duration'] = int(val)
    return conf

def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    wrap.__name__ = f.__name__
    return wrap

# ================= THREAD =================
def expiry_monitor():
    while True:
        now = datetime.now()
        for name, data in list(user_sessions.items()):
            if data['running'] and data['end_time'] != "unlimited":
                if now > data['end_time']:
                    if data['proc']:
                        data['proc'].terminate()
                    user_sessions[name]['running'] = False
                    socketio.emit('status_update', {'running': False, 'user': name})
        eventlet.sleep(2)

threading.Thread(target=expiry_monitor, daemon=True).start()

def stream_logs(proc, name):
    for line in iter(proc.stdout.readline, ''):
        if line:
            socketio.emit('new_log', {'data': line.strip(), 'user': name})

# ================= ROUTES =================
@app.route('/login')
def login():
    return render_template_string(LOGIN_HTML)

@app.route('/api/login_auth', methods=['POST'])
def login_auth():
    data = request.json
    if data.get('username') == "ngu" and data.get('password') == "sikibidiexe453":
        session['logged_in'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/')
@login_required
def index():
    return render_template('index.html')
@app.route('/api/control', methods=['POST'])
@login_required
def bot_control():
    data = request.json
    action = data.get('action')

    if action == 'start':
        proc = subprocess.Popen(
            [sys.executable, '-u', 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        threading.Thread(target=stream_logs, args=(proc, "user"), daemon=True).start()
        return jsonify({"status": "started"})

    return jsonify({"status": "ok"})

# ================= RUN =================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)