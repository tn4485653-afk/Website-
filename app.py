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
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cyber Core | Login</title>
<style>
body{background:#0a0a0a;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif}
.box{background:#111;padding:30px;border-radius:15px;width:300px}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:none;color:#fff}
button{width:100%;padding:10px;background:#00f2fe;border:none;color:#000;font-weight:bold}
</style>
</head>
<body>
<div class="box">
<h2>Login TCP bot</h2>
<input id="u" placeholder="Username">
<input id="p" type="password" placeholder="Password">
<button onclick="login()">Login</button>
<p id="msg"></p>
</div>
<script>
async function login(){
let u=document.getElementById("u").value;
let p=document.getElementById("p").value;
let r=await fetch('/api/login_auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
let d=await r.json();
if(d.status==='success'){location.href='/'}else{msg.innerText='Sai tài khoản';}
}
</script>
</body>
</html>"""

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
    return "<h1>BOT PANEL ONLINE ✅</h1>"

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