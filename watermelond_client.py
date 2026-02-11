import os
import sys
import threading
import time
import socketio
import requests
import logging
import base64
import numpy as np
import pyaudio
import struct
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, render_template_string
from client_config import ClientConfig
import webview


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CLIENT] - %(levelname)s - %(message)s')
logger = logging.getLogger("WatermelonClient")
# Suppress Werkzeug "development server" warning
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from flask_wtf.csrf import CSRFProtect

# Initialize Config
config = ClientConfig()

app = Flask(__name__, static_folder='TangerineUI/static', template_folder='TangerineUI/templates')
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

# Global State
client_agent = None

# --- HTML Templates for Setup ---
SETUP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WatermelonD Client Setup</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --panel-bg: #111827;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-color: #38bdf8;
            --accent-secondary: #818cf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --border-color: #1e293b;
            --error-color: #f87171;
            --success-color: #4ade80;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        .setup-container {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 3rem;
            width: 400px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
        }

        /* Subtle glowing orb effect behind */
        .orb {
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, var(--accent-color) 0%, transparent 70%);
            opacity: 0.1;
            filter: blur(60px);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: -1;
            pointer-events: none;
        }

        h1 {
            text-align: center;
            font-weight: 600;
            color: var(--accent-color);
            margin-top: 0;
            margin-bottom: 2rem;
            font-size: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-shadow: 0 0 20px var(--accent-glow);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
        }

        input[type="text"] {
            width: 100%;
            padding: 12px 16px;
            background: rgba(11, 15, 25, 0.6);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
            box-sizing: border-box;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 15px var(--accent-glow);
            background: rgba(11, 15, 25, 0.8);
        }

        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--accent-color), var(--accent-secondary));
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            margin-top: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(56, 189, 248, 0.5);
        }

        button:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <div class="orb"></div>
    <div class="setup-container">
        <h1>WatermelonD Setup</h1>
        <form method="POST" action="/setup">
            <div class="form-group">
                <label>Server URL</label>
                <input type="text" name="server_url" placeholder="http://192.168.1.50:5000" required value="{{ server_url }}">
            </div>
            <div class="form-group">
                <label>Wake Words (comma separated)</label>
                <input type="text" name="wake_words" placeholder="neo, computadora" required value="{{ wake_words }}">
            </div>
            <button type="submit">Save & Connect</button>
        </form>
    </div>
</body>
</html>
"""

# --- Client Agent (Background Audio Processing) ---
class ClientAgent(threading.Thread):
    def __init__(self, server_url, wake_words):
        super().__init__(daemon=True)
        self.server_url = server_url
        self.wake_words = [w.strip().lower() for w in wake_words.split(',')]
        self.running = True
        self.sio = socketio.Client()
        self.recognizer = None
        self.setup_stt()

    def setup_stt(self):
        try:
            import sherpa_onnx
            
            model_paths = [
                "/app/share/models/sherpa-onnx-whisper-small",
                "models/sherpa/sherpa-onnx-whisper-small",
                "models/sherpa-onnx-whisper-small" 
            ]
            
            model_dir = None
            for p in model_paths:
                if os.path.exists(p):
                    model_dir = p
                    break
            
            if not model_dir:
                logger.error("Sherpa models not found!")
                return

            logger.info(f"Loading Sherpa model from {model_dir}")
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=os.path.join(model_dir, "encoder.onnx"),
                decoder=os.path.join(model_dir, "decoder.onnx"),
                tokens=os.path.join(model_dir, "tokens.txt"),
                language="es",
                task="transcribe",
                num_threads=2
            )
        except Exception as e:
            logger.error(f"Failed to load user STT model: {e}")

    def connect_bus(self):
        try:
            if not self.sio.connected:
                self.sio.connect(self.server_url, transports=['polling', 'websocket'])
                logger.info(f"Connected to Server Bus: {self.server_url}")
        except Exception as e:
            logger.error(f"Bus connection failed: {e}")

    def run(self):
        self.connect_bus()
        
        # Audio Loop (Simplified version of AudioService)
        CHUNK = 1024
        RATE = 16000
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
        stream.start_stream()
        
        logger.info("Listening...")
        
        audio_buffer = []
        is_recording = False
        silence_frames = 0
        THRESHOLD = 500
        SILENCE_LIMIT = 30 # ~1.5 sec silence
        
        while self.running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                shorts = struct.unpack("%dh" % (len(data) / 2), data)
                rms = np.sqrt(np.mean(np.square(shorts)))
                
                if rms > THRESHOLD:
                    if not is_recording:
                        is_recording = True
                        logger.info("Voice detected...")
                    silence_frames = 0
                    audio_buffer.append(data)
                else:
                    if is_recording:
                        silence_frames += 1
                        audio_buffer.append(data)
                        
                if is_recording and silence_frames > SILENCE_LIMIT:
                    # End of phrase
                    logger.info("Processing phrase...")
                    raw_data = b''.join(audio_buffer)
                    self.process_audio(raw_data, RATE)
                    
                    audio_buffer = []
                    is_recording = False
                    silence_frames = 0
                    
            except Exception as e:
                pass
                
    def process_audio(self, raw_data, rate):
        if not self.recognizer: return
        
        # Transcribe
        samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        s = self.recognizer.create_stream()
        s.accept_waveform(rate, samples)
        self.recognizer.decode_stream(s)
        text = s.result.text.strip()
        
        if text:
            logger.info(f"Stt: {text}")
            # Check Wake Word
            triggered = False
            wakeword = ""
            for cur_ww in self.wake_words:
                if cur_ww in text.lower():
                    triggered = True
                    wakeword = cur_ww
                    break
            
            if triggered:
                logger.info(f"Wake Word '{wakeword}' detected!")

                msg = text.lower().replace(wakeword, "").strip()
                if msg:
                   self.emit_utterance(msg)
            else:
                 logger.info("No wake word found in: " + text)

    def emit_utterance(self, text):
        if self.sio.connected:

            self.sio.emit('message', {
                "type": "recognizer_loop:utterance",
                "data": {"utterances": [text]},
                "context": {"source": "flatpak_client"}
            })
            logger.info(f"Sent command: {text}")
        else:
             self.connect_bus() # Try reconnect



@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        server_url = request.form.get('server_url')
        wake_words = request.form.get('wake_words')
        
        # Validate URL
        if not server_url.startswith('http'):
            server_url = 'http://' + server_url
            
        config.set('server_url', server_url)
        config.set('wake_words', wake_words)
        
        # Restart Agent if running logic was complex, but simple way is just start it now
        start_agent()
        
        return redirect(url_for('index'))
        
    return render_template_string(SETUP_HTML, server_url=config.get('server_url', ''), wake_words=config.get('wake_words', ''))

@app.route('/')
def index():
    if not config.is_configured():
        return redirect(url_for('setup'))
    

    return render_template('dashboard.html', page='dashboard', socket_url=config.get('server_url'))



@app.context_processor
def inject_globals():
    return dict(socket_url=config.get('server_url', ''))

# We copy the route structure from original app.py essentially
# Route Configuration mapping URL path -> Endpoint & Template
ROUTES_CONFIG = {
    'dashboard': {'endpoint': 'dashboard', 'template': 'dashboard.html'},
    'services': {'endpoint': 'services', 'template': 'services.html'},
    'docker': {'endpoint': 'docker', 'template': 'docker.html'},
    'tasks': {'endpoint': 'tasks_page', 'template': 'tasks.html'},     # Template expects 'tasks_page'
    'network': {'endpoint': 'network', 'template': 'network.html'},
    'actions': {'endpoint': 'actions', 'template': 'actions.html'},
    'terminal': {'endpoint': 'terminal', 'template': 'terminal.html'},
    'logs': {'endpoint': 'logs', 'template': 'logs.html'},
    'monitor': {'endpoint': 'monitor', 'template': 'monitor.html'},
    'speech': {'endpoint': 'speech', 'template': 'speech.html'},
    'ssh': {'endpoint': 'ssh_page', 'template': 'ssh.html'},         # Template expects 'ssh_page'
    'explorer': {'endpoint': 'explorer', 'template': 'explorer.html'},
    'knowledge': {'endpoint': 'knowledge', 'template': 'knowledge.html'},
    'skills': {'endpoint': 'skills', 'template': 'skills.html'},
    'training': {'endpoint': 'training', 'template': 'training.html'},
    'face': {'endpoint': 'face', 'template': 'face.html'},
    'agents': {'endpoint': 'agents', 'template': 'agents.html'},     # Added missing route
}

for url_path, conf in ROUTES_CONFIG.items():
    # Use default arguments to capture the values in the lambda closure
    app.add_url_rule(
        f'/{url_path}', 
        conf['endpoint'], 
        lambda t=conf['template'], p=url_path: render_template(t, page=p)
    )

@app.route('/logout')
def logout():
    # Allow user to "reset" or just go back to setup/index
    # For now, just redirect to index
    return redirect(url_for('index'))

# Specialized Settings Route (needs data)
@app.route('/settings')
def settings():
    server_url = config.get('server_url')
    if not server_url: return redirect(url_for('setup'))
    try:
        resp = requests.get(f"{server_url}/api/config/get", verify=False, timeout=2)
        data = resp.json()
        return render_template('settings.html', page='settings', config=data.get('config',{}), voices=data.get('voices',[]), models=data.get('models',[]))
    except:
        return render_template('settings.html', page='settings', error="Remote Server Connect Error")

# API Proxy
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    server_url = config.get('server_url')
    if not server_url: return jsonify({'error': 'Not configured'}), 503
    
    url = f"{server_url}/api/{path}"
    try:
        if request.method == 'GET':
            resp = requests.get(url, params=request.args)
        elif request.method == 'POST':
            if request.is_json:
                resp = requests.post(url, json=request.json)
            else:
                resp = requests.post(url, data=request.form, files=request.files)

        
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start_agent():
    global client_agent
    if client_agent and client_agent.is_alive():
        return # Already running
        
    s_url = config.get('server_url')
    ww = config.get('wake_words')
    
    if s_url and ww:
        client_agent = ClientAgent(s_url, ww)
        client_agent.start()

if __name__ == '__main__':
    # Start Agent if configured
    if config.is_configured():
        start_agent()
        
    # Start Flask in a background thread
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False))
    t.daemon = True
    t.start()
    
    # Wait a bit for server to start
    time.sleep(1)

    webview.create_window('WatermelonD Client', 'http://127.0.0.1:8000', width=1200, height=800, resizable=True)
    webview.start()
