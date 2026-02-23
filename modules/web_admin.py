from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file, send_from_directory, abort
import base64
import platform
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import functools
import os
import json
import subprocess
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

# Importar el módulo brain explícitamente para acceder a learn_alias si es necesario mediante importación directa o asegurar que la bd lo tiene
from modules.brain import Brain

from modules.sysadmin import SysAdminManager
from modules.database import DatabaseManager
from modules.config_manager import ConfigManager
from modules.ssh_manager import SSHManager
from modules.ssh_manager import SSHManager
from modules.file_manager import FileManager
from modules.wifi_manager import WifiManager
from modules.dashboard_data import DashboardDataManager
from modules.knowledge_base import KnowledgeBase
from modules.scheduler_manager import SchedulerManager

app = Flask(__name__, template_folder='../TangerineUI/templates', static_folder='../TangerineUI/static')

config_manager = ConfigManager()

# Clave Secreta Persistente
secret_key = config_manager.get('secret_key')
if not secret_key:
    secret_key = os.urandom(24).hex()
    config_manager.set('secret_key', secret_key)

app.secret_key = secret_key

# Inicializar Protección CSRF
csrf = CSRFProtect(app)

# Inicializar SocketIO
# Revertir a threading para compatibilidad con PyAudio/Voice Threads
# Se añadieron configuraciones de keepalive para prevenir desconexiones
socketio = SocketIO(
    app, 
    async_mode='threading', 
    cors_allowed_origins="*",
    ping_timeout=60,          # Esperar 60s por pong antes de desconectar
    ping_interval=25,         # Enviar ping cada 25s
    engineio_logger=False,
    logger=False
)

# Inicializar Limitador de Tasa
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10000 per day", "1000 per hour"],
    storage_uri="memory://"  # Usar Redis en producción: "redis://localhost:6379"
)

# Estado Global del Sistema
AUDIO_STATUS = {'output': False, 'input': False}

def set_audio_status(output_enabled, input_enabled):
    global AUDIO_STATUS
    AUDIO_STATUS['output'] = output_enabled
    AUDIO_STATUS['input'] = input_enabled

@app.context_processor
def inject_status():
    return dict(audio_status=AUDIO_STATUS, socket_url="")

@socketio.on('message')
def handle_message(data):
    """Retransmite mensajes broadcast a todos los clientes conectados (Bus)."""
    # print(f"DEBUG: Transmitiendo mensaje: {data}")
    emit('message', data, broadcast=True)

from modules.bus_client import BusClient

sys_admin = SysAdminManager()
db = DatabaseManager()
ssh_manager = SSHManager()
file_manager = FileManager()
wifi_manager = WifiManager()
dashboard_manager = DashboardDataManager(config_manager)
dashboard_manager = DashboardDataManager(config_manager)
knowledge_base = KnowledgeBase() # Sistema RAG
scheduler_manager = SchedulerManager(app) # Programador de Tareas
brain = Brain() # Inicializar instancia Brain independiente para operaciones de Web Admin

# --- Integración de Cliente de Bus ---
bus = BusClient(name="WebAdmin")

def on_mic_status(message):
    data = message.get('data', {})
    muted = data.get('muted', False)
    # Actualizar estado global
    AUDIO_STATUS['input'] = not muted
    
    # Retransmitir a Clientes Web vía SocketIO
    update_face('status_update', {'mic_muted': muted})
    # También emitir evento específico para el dashboard
    try:
        socketio.emit('audio_status', AUDIO_STATUS)
    except:
        pass

bus.on('mic:status', on_mic_status)
# bus.connect()  <-- Arreglo Deadlock: Dejar que run_forever lo maneje en hilo
# Ejecutar bus en hilo en segundo plano
import threading
# threaded=True coincide con async_mode='threading' pero nos movemos a eventlet para estabilidad
# Nota: Asegurar que eventlet NO esté "monkey-patched" globalmente en NeoCore.py para evitar problemas con PyAudio.
import threading
threading.Thread(target=bus.run_forever, daemon=True).start()

# --- Cabeceras de Seguridad y Middlewares ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# --- API del Buscador y Visor ---

@app.route('/api/viewer/serve/<encoded_path>')
def serve_viewer_content(encoded_path):
    """
    Sirve archivos locales para el Visor PiP.
    Requiere que la ruta esté codificada en Base64 para evitar problemas de URL.
    Aplica Lista Blanca Estricta.
    """
    if not session.get('logged_in'):
        return abort(403)
        
    try:
        decoded_path = base64.urlsafe_b64decode(encoded_path).decode('utf-8')
        
        # Controles de Seguridad
        if not os.path.exists(decoded_path):
            return abort(404)
            
        # Lista Blanca de Extensiones (Doble Comprobación)
        ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.mp3', '.wav', '.ogg', '.pdf', '.md', '.txt', '.log', '.json', '.csv']
        ext = os.path.splitext(decoded_path)[1].lower()
        if ext not in ALLOWED_EXTS:
            return abort(403, description="File type not allowed")
            
        return send_file(decoded_path)
    except Exception as e:
        print(f"Error serving file: {e}")
        return abort(500)

@app.route('/api/settings/user_docs', methods=['GET', 'POST'])
def settings_user_docs():
    """
    Leer/Escribir config/user_docs.json para el Editor de Ajustes.
    """
    if not session.get('logged_in'):
        return abort(403)
        
    config_path = "config/user_docs.json"
    
    if request.method == 'GET':
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({})
        
    if request.method == 'POST':
        try:
            new_data = request.json
            # ¿Validar estructura? Por ahora se asume que el usuario sabe o el frontend valida.
            with open(config_path, 'w') as f:
                json.dump(new_data, f, indent=2)
            return jsonify({"status": "success", "message": "Docs updated"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


# Limitador de Tasa de Inicio de Sesión simple en memoria
login_attempts = {}

def rate_limit_login(func):
    """Limitar a 5 intentos de login por minuto por IP."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        
        # Limpiar intentos antiguos
        if ip in login_attempts:
            login_attempts[ip] = [t for t in login_attempts[ip] if now - t < 60]
            
        if len(login_attempts.get(ip, [])) >= 5:
            # flash('Demasiados intentos. Espera 1 minuto.', 'danger')
            from flask import make_response
            return make_response(render_template('login.html', error='Demasiados intentos. Espera 1 minuto.'), 429)
            
        return func(*args, **kwargs)
    return wrapper

def login_required(view):
    """Decorador para proteger rutas que requieren autenticación."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('logged_in') is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def index():
    """Ruta raíz: redirige al dashboard o al login."""
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@rate_limit_login
def login():
    """Página de inicio de sesión."""
    error = None
    if request.method == 'POST':
        user = config_manager.get('admin_user', 'admin')
        stored_pass = config_manager.get('admin_pass', 'admin')
        
        # Comprobar si la contraseña guardada es texto plano (migración básica)
        # Los hashes de Werkzeug normalmente empiezan por el método (pbkdf2:...)
        if not stored_pass.startswith(('pbkdf2:', 'scrypt:')):
            # Es texto plano, hashearlo inmediatamente
            hashed = generate_password_hash(stored_pass)
            config_manager.set('admin_pass', hashed)
            stored_pass = hashed
            
        username_input = request.form['username']
        password_input = request.form['password']
        
        if username_input == user and check_password_hash(stored_pass, password_input):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            # Registrar intento
            ip = request.remote_addr
            if ip not in login_attempts: login_attempts[ip] = []
            login_attempts[ip].append(time.time())
            
            error = 'Credenciales inválidas. Inténtalo de nuevo.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- PÁGINAS ---

@app.route('/dashboard')
@login_required
def dashboard():
    """Renderiza el dashboard principal."""
    return render_template('dashboard.html', page='dashboard')



@app.route('/tasks')
@login_required
def tasks_page():
    """Renderiza la página de tareas programadas."""
    return render_template('tasks.html', page='tasks')

@app.route('/network')
@login_required
def network():
    """Renderiza la página de herramientas de red."""
    return render_template('network.html', page='network')

@app.route('/actions')
@login_required
def actions():
    """Renderiza la página de acciones rápidas."""
    return render_template('actions.html', page='actions')

@app.route('/terminal')
@login_required
def terminal():
    """Renderiza la terminal web."""
    return render_template('terminal.html', page='terminal')

@app.route('/logs')
@login_required
def logs():
    """Renderiza el visor de logs."""
    return render_template('logs.html', page='logs')

@app.route('/monitor')
@login_required
def monitor():
    """Renderiza la página de monitorización del sistema."""
    return render_template('monitor.html', page='monitor')

@app.route('/speech')
@login_required
def speech():
    """Renderiza el historial de voz."""
    return render_template('speech.html', page='speech')

from modules.system_info import get_system_info

# ... imports ...

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Renderiza y procesa la página de configuración."""
    config = config_manager.get_all() or {}
    
    # Listar voces disponibles
    voices_dir = os.path.join(os.getcwd(), 'piper', 'voices')
    available_voices = []
    if os.path.exists(voices_dir):
        for f in os.listdir(voices_dir):
            if f.endswith('.onnx'):
                available_voices.append(f)
    
    # Listar modelos de IA disponibles (GGUF)
    models_dir = os.path.join(os.getcwd(), 'models')
    available_models = []
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            if f.endswith('.gguf'):
                available_models.append(f)

    if request.method == 'POST':
        config_manager.set('admin_user', request.form['username'])
        
        # Solo actualizar contraseña si se proporciona y no está vacía
        new_pass = request.form.get('password')
        if new_pass and new_pass.strip():
            config_manager.set('admin_pass', generate_password_hash(new_pass))
            
        config_manager.set('wake_word', request.form['wake_word'])
        config_manager.set('neo_ssh_enabled', 'neo_ssh_enabled' in request.form)
        
        # CSS Personalizado
        custom_css = request.form.get('custom_css', '')
        config_manager.set('custom_css', custom_css)

        # Manejar Modelo IA
        selected_model = request.form.get('ai_model')
        if selected_model:
            full_model_path = os.path.join(models_dir, selected_model)
            config_manager.set('ai_model_path', full_model_path)

        # Manejar Modelo TTS
        selected_voice = request.form.get('tts_model')
        if selected_voice:
            full_path = os.path.join(voices_dir, selected_voice)
            current_tts = config.get('tts', {}) if config else {}
            current_tts['piper_model'] = full_path
            config_manager.set('tts', current_tts)

        flash('Configuración guardada correctamente.', 'success')
        return redirect(url_for('settings'))
    
    # Construir info del sistema completa
    raw_info = sys_admin.get_system_info()
    
    # Asegurar que todas las claves requeridas existen
    system_info = raw_info if raw_info else {}
    
    # Info de la APP
    if 'app' not in system_info:
        system_info['app'] = {}
    system_info['app']['name'] = 'WatermelonD'
    system_info['app']['version'] = '2.5.0' # Por hacer: Obtener de la config
    system_info['app']['branch'] = get_git_branch()
    
    import platform # Añadido para la obtención de info del sistema
    
    # Info del SO
    if 'os' not in system_info:
        system_info['os'] = {
            'system': system_info.get('system', 'Unknown'),
            'release': system_info.get('release', 'Unknown'),
            'version': system_info.get('version', 'Unknown'),
            'architecture': system_info.get('machine', 'Unknown'),
            'processor': platform.processor() or 'Unknown'
        }
        
    # Info de Python
    if 'python' not in system_info:
        system_info['python'] = {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'compiler': platform.python_compiler()
        }
    
    # Info de Librerías
    if 'libraries' not in system_info:
        import flask
        import flask_socketio
        import jinja2
        import platform # Arreglar NameError
        
        try:
            import importlib.metadata
            fs_version = importlib.metadata.version('Flask-SocketIO')
        except:
            fs_version = getattr(flask_socketio, '__version__', 'unknown')
            
        system_info['libraries'] = {
            'python': platform.python_version(),
            'flask': getattr(flask, '__version__', 'unknown'),
            'flask_socketio': fs_version,
            'jinja2': getattr(jinja2, '__version__', 'unknown')
        }

    return render_template('settings.html', page='settings', config=config, voices=available_voices, models=available_models, sys_info=system_info)

@app.route('/ssh')
@login_required
def ssh_page():
    """Renderiza la página de gestión SSH."""
    if not config_manager.get('neo_ssh_enabled', False):
        return redirect(url_for('settings'))
    return render_template('ssh.html', page='ssh')

@app.route('/explorer')
@login_required
def explorer():
    """Renderiza el explorador de archivos."""
    return render_template('explorer.html', page='explorer')

@app.route('/knowledge')
@login_required
def knowledge():
    """Renderiza la gestión de conocimientos."""
    return render_template('knowledge.html', page='knowledge')

@app.route('/skills')
@login_required
def skills():
    """Renderiza el gestor de habilidades."""
    return render_template('skills.html', page='skills', config=config_manager.get_all())

@app.route('/training')
@login_required
def training():
    """Renderiza la página de entrenamiento."""
    return render_template('training.html', page='training', config=config_manager.get_all())

@app.route('/agents')
@login_required
def agents():
    """Renderiza la página de gestión de agentes MQTT."""
    return render_template('agents.html', page='agents')

@app.route('/face')
def face():
    """Renderiza la interfaz visual (Ojos). No requiere login para funcionar en modo Kiosk."""
    return render_template('face.html')

def update_face(state, data=None):
    """Envía una actualización de estado a la interfaz facial."""
    try:
        if data is None:
            data = {}
        print(f"DEBUG: Emitting face_update: {state}")
        socketio.emit('face_update', {'state': state, 'data': data})
    except Exception as e:
        print(f"Error updating face: {e}")

# --- API ---

@app.route('/api/restart', methods=['POST'])
@login_required
def restart_system():
    """API para reiniciar el servicio (o sistema si es posible)."""
    try:
        # Intentar primero el reinicio del servicio de usuario (reinicio suave)
        subprocess.Popen(['systemctl', '--user', 'restart', 'neo.service'])
        return jsonify({'status': 'success', 'message': 'Reiniciando servicio Neo...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_git_branch():
    """Devuelve la rama actual de git."""
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        return branch
    except:
        return "unknown"

@app.route('/api/update', methods=['POST'])
@login_required
def update_system():
    """Ejecuta git pull para la rama actual y reinicia el servicio."""
    try:
        branch = get_git_branch()
        app_logger.info(f"Updating system from branch: {branch}")
        
        # 1. Hacer Git Pull a la Rama Específica
        cmd = ['git', 'pull', 'origin', branch]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
             return jsonify({'success': False, 'message': f'Git Pull Error ({branch}): {result.stderr}'})

        # 2. Actualizar Submódulos
        subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], capture_output=True)

        # 3. Reiniciar Servicio
        subprocess.Popen(['systemctl', '--user', 'restart', 'neo.service'])
        return jsonify({'success': True, 'message': f'Actualizado desde {branch}. Reiniciando... \n{result.stdout}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/update/check', methods=['GET'])
@login_required
def check_updates():
    """Verifica si hay cambios remotos sin aplicar."""
    try:
        subprocess.run(['git', 'fetch'], capture_output=True)
        local_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        remote_hash = subprocess.check_output(['git', 'rev-parse', '@{u}'], text=True).strip()
        
        has_updates = local_hash != remote_hash
        branch = get_git_branch()
        
        return jsonify({
            'has_updates': has_updates,
            'branch': branch,
            'local_hash': local_hash[:7],
            'remote_hash': remote_hash[:7]
        })
    except Exception as e:
        return jsonify({'has_updates': False, 'error': str(e)})

@app.route('/api/audio/toggle', methods=['POST'])
@login_required
def api_audio_toggle():
    """Alterna el estado de silenciamiento del micrófono."""
    bus.emit('mic:toggle', {})
    # Devolver estado optimista, la confirmación real viene vía socketio
    new_state = not AUDIO_STATUS['input']
    AUDIO_STATUS['input'] = new_state # Actualización local optimista
    return jsonify({'success': True, 'muted': not new_state})

@app.route('/api/audio/status', methods=['GET'])
@login_required
def api_audio_status():
    """Devuelve el estado actual de audio."""
    # Forzar petición de refresco solo si está conectado para evitar spam en logs
    if bus.connected:
        bus.emit('mic:get_status', {})
    return jsonify(AUDIO_STATUS)

@app.route('/api/stats')
@login_required
def api_stats():
    """API que devuelve estadísticas del sistema en JSON."""
    return jsonify({
        'cpu_temp': sys_admin.get_cpu_temp(),
        'cpu_usage': sys_admin.get_cpu_usage(),
        'ram_usage': sys_admin.get_ram_usage(),
        'disk_usage': sys_admin.get_disk_usage()
    })

@app.route('/api/logs')
@login_required
def api_logs():
    """API que devuelve las últimas 100 líneas del log."""
    log_content = ""
    try:
        with open('logs/app.log', 'r') as f:
            lines = f.readlines()[-100:]
            log_content = "".join(lines)
    except FileNotFoundError:
        log_content = "Log file not found."
    return jsonify({'logs': log_content})

@app.route('/api/ollama/status')
@login_required
def api_ollama_status():
    """Devuelve estado y logs de Ollama."""
    running = False
    try:
        subprocess.check_call(['systemctl', 'is-active', '--quiet', 'ollama'])
        running = True
    except:
        running = False
        
    logs = ""
    try:
        # Obtener las últimas 50 líneas de los logs de ollama
        result = subprocess.run(['journalctl', '-u', 'ollama', '-n', '50', '--no-pager'], capture_output=True, text=True)
        logs = result.stdout
    except Exception as e:
        logs = str(e)
        
    return jsonify({'running': running, 'logs': logs})

@app.route('/api/logs/read', methods=['POST'])
@login_required
def api_logs_read():
    """Lee un fichero de log específico."""
    filename = request.json.get('file')
    content = ""
    
    if filename == 'neo.service':
        try:
            result = subprocess.run(['journalctl', '-u', 'neo.service', '-n', '200', '--no-pager'], capture_output=True, text=True)
            content = result.stdout
        except Exception as e:
            content = str(e)
    elif filename == 'app.log':
        try:
            if os.path.exists('logs/app.log'):
                with open('logs/app.log', 'r') as f:
                    content = f.read()[-10000:] # Últimos 10k caracteres
            else:
                content = "Log file not found."
        except Exception as e:
            content = str(e)
            
    return jsonify({'content': content})

@app.route('/api/speech_history')
@login_required
def api_speech_history():
    """API que devuelve las últimas interacciones de voz."""
    interactions = db.get_recent_interactions(limit=50)
    # Convertir filas de SQLite a dicts
    data = []
    for row in interactions:
        data.append({
            'timestamp': row['timestamp'],
            'user': row['user_input'],
            'neo': row['neo_response'],
            'intent': row['intent_name']
        })
    return jsonify(data)



@app.route('/api/network', methods=['GET'])
@login_required
def api_network():
    """API que devuelve información de red."""
    return jsonify(sys_admin.get_network_info())

@app.route('/api/network/speedtest', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def api_network_speedtest():
    """API para ejecutar test de velocidad."""
    return jsonify(sys_admin.run_speedtest())

@app.route('/api/wifi/scan', methods=['GET'])
@login_required
@limiter.limit("10 per minute")
def api_wifi_scan():
    """API para escanear redes WiFi."""
    result = wifi_manager.scan()
    
    # Si scan() devuelve un diccionario de error, pasarlo
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result)
    
    # De lo contrario, devolver lista de redes
    return jsonify(result)

@app.route('/api/wifi/connect', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def api_wifi_connect():
    """API para conectar a una red WiFi."""
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    
    if not ssid or not password:
        return jsonify({'success': False, 'message': 'SSID y contraseña requeridos'})
        
    success, msg = wifi_manager.connect(ssid, password)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/dashboard/data', methods=['GET'])
def api_dashboard_data():
    """API para datos del dashboard (Smart Mirror). No requiere login para funcionar en modo Kiosk."""
    return jsonify(dashboard_manager.get_all_data())

@app.route('/api/monitor/processes', methods=['GET'])
@login_required
def api_monitor_processes():
    """API que devuelve los procesos top."""
    return jsonify(sys_admin.get_top_processes())

@app.route('/api/config/experimental', methods=['POST'])
@login_required
def update_experimental_config():
    try:
        data = request.json
        feature = data.get('feature')
        enabled = data.get('enabled')
        
        current = config_manager.get('experimental', {})
        current[feature] = enabled
        config_manager.set('experimental', current)
        
        return jsonify({'success': True, 'message': f'{feature} updated.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config/save', methods=['POST'])
@login_required
def api_config_save():
    """API para guardar configuración raw."""
    try:
        new_config = request.json
        # Validar JSON básico (ya lo hace request.json pero por si acaso)
        if not isinstance(new_config, dict):
            return jsonify({'success': False, 'message': 'Formato inválido'})
            
        # Guardar usando ConfigManager (necesitamos un método save_all o similar)
        # ConfigManager normalmente guarda clave a clave, o carga de disco.
        # Vamos a asumir que podemos escribir el fichero directamente por ahora
        # o iterar sobre las claves.
        
        # Mejor opción: Guardar a disco directamente para reemplazar todo
        with open('config/config.json', 'w') as f:
            json.dump(new_config, f, indent=4)
            
        # Recargar config en memoria
        config_manager.load_config()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/terminal', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_terminal():
    """API para ejecutar comandos en la terminal con estado (cwd) por sesión."""
    data = request.json
    cmd = data.get('command')
    term_id = str(data.get('term_session', '1')) # Por defecto a sesión 1
    
    # Inicializar store de sesiones
    if 'term_cwds' not in session:
        session['term_cwds'] = {}
        
    # Inicializar CWD para esta sesión específica
    if term_id not in session['term_cwds']:
        session['term_cwds'][term_id] = os.path.expanduser('~')
        session.modified = True 
        
    current_cwd = session['term_cwds'][term_id]

    # Seguridad básica
    if 'nano' in cmd or 'vim' in cmd or 'top' in cmd:
        return jsonify({'success': False, 'output': 'Comandos interactivos no soportados.', 'cwd': current_cwd})
    
    # Manejo especial para 'cd'
    if cmd.strip().startswith('cd '):
        target_dir = cmd.strip()[3:].strip()
        # Resolver ruta relativa
        new_path = os.path.abspath(os.path.join(current_cwd, target_dir))
        
        if os.path.isdir(new_path):
            session['term_cwds'][term_id] = new_path
            session.modified = True
            return jsonify({'success': True, 'output': '', 'cwd': new_path})
        else:
            return jsonify({'success': False, 'output': f"cd: {target_dir}: No such file or directory", 'cwd': current_cwd})
    
    # Ejecutar comando normal en el CWD actual
    success, output = sys_admin.run_command(cmd, cwd=current_cwd)
    return jsonify({'success': success, 'output': output, 'cwd': current_cwd})

@app.route('/api/terminal/complete', methods=['POST'])
@login_required
def api_terminal_complete():
    """API para autocompletado de archivos (Tab)."""
    data = request.json
    full_command = data.get('command', '')
    term_id = str(data.get('term_session', '1'))
    
    if 'term_cwds' not in session or term_id not in session['term_cwds']:
        # Alternativa
        current_cwd = os.path.expanduser('~')
    else:
        current_cwd = session['term_cwds'][term_id]
    
    # Extraer la última palabra (token) que es lo que se está completando
    # Ejemplo: "ls Doc" -> "Doc"
    # Ejemplo: "cd /etc/sys" -> "/etc/sys"
    if not full_command:
        return jsonify({'matches': []})
        
    tokens = full_command.split()
    if full_command.endswith(' '):
        # Si termina en espacio, estamos buscando en el directorio actual o empezando nuevo argumento
        partial = ""
    else:
        partial = tokens[-1]
        
    matches = sys_admin.get_file_completions(partial, current_cwd)
    return jsonify({'matches': matches, 'partial': partial})

@app.route('/api/actions', methods=['POST'])
@login_required
def api_actions():
    """API para ejecutar acciones rápidas predefinidas."""
    action_id = request.json.get('id')
    commands = {
        'update': 'sudo apt-get update && sudo apt-get upgrade -y', # Debian/Pi
        'clean': 'sudo apt-get clean && sudo apt-get autoremove -y',
        'backup': 'tar -czf backup_openkompai.tar.gz .',
        'net_restart': 'sudo systemctl restart networking',
        'update_models': 'bash resources/tools/update_grape_models.sh'
    }
    
    # Detectar Fedora para comandos diferentes
    if os.path.exists('/etc/fedora-release'):
        commands['update'] = 'sudo dnf update -y'
        commands['clean'] = 'sudo dnf clean all'

    if action_id in commands:
        success, output = sys_admin.run_command(commands[action_id])
        return jsonify({'success': success, 'output': output})
    
    return jsonify({'success': False, 'output': 'Acción desconocida'})

# --- API SSH ---

@app.route('/api/ssh/list', methods=['GET'])
@login_required
def api_ssh_list():
    """Devuelve la lista de servidores."""
    return jsonify(ssh_manager.servers)

@app.route('/api/ssh/add', methods=['POST'])
@login_required
def api_ssh_add():
    """Añade un nuevo servidor."""
    data = request.json
    try:
        ssh_manager.add_server(
            alias=data['alias'],
            host=data['host'],
            user=data['user'],
            port=data.get('port', 22),
            key_path=data.get('key_path'),
            password=data.get('password')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/ssh/delete', methods=['POST'])
@login_required
def api_ssh_delete():
    """Elimina un servidor."""
    data = request.json
    if ssh_manager.remove_server(data['alias']):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Servidor no encontrado'})



    return jsonify({'success': False, 'message': 'Servidor no encontrado'})


@app.route('/api/command/inject', methods=['POST'])
def api_command_inject():
    """Inyecta un comando de texto en el sistema a través del Bus. No requiere autenticación para el modo kiosco."""
    try:
        data = request.json
        text = data.get('text')
        if not text:
            return jsonify({'success': False, 'message': 'No text provided'})
            
        # Emitir a NeoCore
        bus.emit('command:inject', {'text': text})
        return jsonify({'success': True, 'message': f"Sent: {text}"})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- API DE AGENTES MQTT ---

@app.route('/api/mqtt/agents', methods=['GET'])
@login_required
def api_mqtt_agents():
    """Devuelve la lista de agentes MQTT registrados y su estado."""
    mqtt_config = config_manager.get('mqtt', {})
    agents = mqtt_config.get('agents', {})
    
    # Obtener estado en vivo del administrador MQTT si está disponible
    # Por ahora, devolveremos los datos del agente almacenados
    return jsonify(agents)

@app.route('/api/mqtt/broker/info', methods=['GET'])
@login_required
def api_mqtt_broker_info():
    """Devuelve información del broker MQTT."""
    import socket
    
    mqtt_config = config_manager.get('mqtt', {})
    broker_address = mqtt_config.get('broker_address', '0.0.0.0')
    broker_port = mqtt_config.get('broker_port', 1883)
    
    # Obtener direcciones IP locales
    def get_local_ips():
        """Obtener todas las direcciones IP locales, filtrando loopback"""
        ips = []
        try:
            # Método 1: Conectar a un DNS público para encontrar la ruta
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
            if primary_ip and not primary_ip.startswith('127.'):
                ips.append(primary_ip)
        except:
            pass
            
        try:
            # Método 2: Obtener todas las interfaces a través de netifaces (mejor) o fallback a hostname
            import netifaces as ni
            for interface in ni.interfaces():
                try:
                    addrs = ni.ifaddresses(interface)
                    if ni.AF_INET in addrs:
                        for addr in addrs[ni.AF_INET]:
                            ip = addr['addr']
                            if ip and not ip.startswith('127.') and ip not in ips:
                                ips.append(ip)
                except:
                    pass
        except ImportError:
            # Alternativa para cuando netifaces no está instalado
            try:
                hostname = socket.gethostname()
                host_ips = socket.gethostbyname_ex(hostname)[2]
                for ip in host_ips:
                    if ip and not ip.startswith('127.') and ip not in ips:
                        ips.append(ip)
            except:
                pass
        
        return ips
    
    local_ips = get_local_ips()
    
    return jsonify({
        'broker_address': broker_address,
        'broker_port': broker_port,
        'local_ips': local_ips,
        'enabled': mqtt_config.get('enabled', True)
    })

@app.route('/api/mqtt/agent/register', methods=['POST'])
@login_required
def api_mqtt_agent_register():
    """Registrar un nuevo agente MQTT."""
    data = request.json
    agent_id = data.get('agent_id')
    
    if not agent_id:
        return jsonify({'success': False, 'message': 'agent_id is required'})
    
    mqtt_config = config_manager.get('mqtt', {})
    agents = mqtt_config.get('agents', {})
    
    # Añadir o actualizar agente
    agents[agent_id] = {
        'id': agent_id,
        'registered_at': time.time(),
        'last_seen': time.time(),
        'status': 'registered'
    }
    
    mqtt_config['agents'] = agents
    config_manager.set('mqtt', mqtt_config)
    
    return jsonify({'success': True, 'agent': agents[agent_id]})

@app.route('/api/mqtt/agent/<agent_id>', methods=['DELETE'])
@login_required
def api_mqtt_agent_delete(agent_id):
    """Eliminar/desregistrar un agente MQTT."""
    mqtt_config = config_manager.get('mqtt', {})
    agents = mqtt_config.get('agents', {})
    
    if agent_id in agents:
        del agents[agent_id]
        mqtt_config['agents'] = agents
        config_manager.set('mqtt', mqtt_config)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Agent not found'})

@app.route('/api/mqtt/generate_installer', methods=['POST'])
@login_required
def api_mqtt_generate_installer():
    """Generar un script de instalación personalizado con IP del broker preconfigurada."""
    try:
        mqtt_config = config_manager.get('mqtt', {})
        broker_port = mqtt_config.get('broker_port', 1883)
        
        # Obtener IP local
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        broker_ip = s.getsockname()[0]
        s.close()
        
        # Leer la plantilla del instalador
        installer_path = os.path.join(os.getcwd(), 'modules', 'BerryConnect', 'PiZero', 'install.sh')
        if not os.path.exists(installer_path):
            return jsonify({'success': False, 'message': 'Installer template not found'})
        
        with open(installer_path, 'r') as f:
            installer_content = f.read()
        
        # Crear versión preconfigurada
        preconfigured = installer_content.replace(
            'BROKER_IP=${BROKER_IP:-192.168.1.100}',
            f'BROKER_IP={broker_ip}'
        ).replace(
            'BROKER_PORT=${BROKER_PORT:-1883}',
            f'BROKER_PORT={broker_port}'
        )
        
        return jsonify({
            'success': True,
            'installer': preconfigured,
            'broker_ip': broker_ip,
            'broker_port': broker_port
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mqtt/agent/<agent_id>/command', methods=['POST'])
@login_required
def api_mqtt_send_command(agent_id):
    """Enviar un comando a un agente específico."""
    try:
        from modules.mqtt_manager import mqtt_manager
        
        data = request.json
        command = data.get('command')
        params = data.get('params', {})
        
        if not command:
            return jsonify({'success': False, 'message': 'Command is required'})
        
        # Validar comando
        valid_commands = ['ping', 'get_status', 'reboot', 'shutdown', 'restart_agent', 'update_config']
        if command not in valid_commands:
            return jsonify({'success': False, 'message': f'Invalid command. Valid: {valid_commands}'})
        
        # Enviar comando a través del administrador MQTT
        if hasattr(bus, 'mqtt_manager') and bus.mqtt_manager:
            command_id = bus.mqtt_manager.send_command(agent_id, command, params)
            if command_id:
                return jsonify({
                    'success': True,
                    'command_id': command_id,
                    'message': f'Command {command} sent to {agent_id}'
                })
            else:
                return jsonify({'success': False, 'message': 'MQTT not connected'})
        else:
            return jsonify({'success': False, 'message': 'MQTT manager not available'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- API DE SKILLS ---

@app.route('/api/skills', methods=['GET'])
@login_required
def api_skills_list():
    """Devuelve la lista de skills y su estado."""
    from modules.utils import load_json_data
    skills_config = load_json_data('config/skills.json') or {}
    return jsonify(skills_config)

@app.route('/api/skills/toggle', methods=['POST'])
@login_required
def api_skills_toggle():
    """Activa o desactiva una skill."""
    data = request.json
    skill_name = data.get('name')
    enabled = data.get('enabled')
    
    if not skill_name:
        return jsonify({'success': False, 'message': 'Nombre de skill requerido'})

    try:
        # Cargar, modificar, guardar
        skills_path = 'config/skills.json'
        with open(skills_path, 'r') as f:
            skills_config = json.load(f)
        
        if skill_name in skills_config:
            skills_config[skill_name]['enabled'] = enabled
            
            with open(skills_path, 'w') as f:
                json.dump(skills_config, f, indent=4)
                
            return jsonify({'success': True})
        else:
             return jsonify({'success': False, 'message': 'Skill no encontrada'})
             
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/skills/save_config', methods=['POST'])
@login_required
def api_skills_save_config():
    """Guarda la configuración avanzada de una skill."""
    data = request.json
    skill_name = data.get('name')
    new_config = data.get('config')
    
    if not skill_name or new_config is None:
        return jsonify({'success': False, 'message': 'Datos incompletos'})

    try:
        skills_path = 'config/skills.json'
        with open(skills_path, 'r') as f:
            skills_config = json.load(f)
        
        if skill_name in skills_config:
            skills_config[skill_name]['config'] = new_config
            
            with open(skills_path, 'w') as f:
                json.dump(skills_config, f, indent=4)
                
            return jsonify({'success': True})
        else:
             return jsonify({'success': False, 'message': 'Skill no encontrada'})
             
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- API DE ENTRENAMIENTO NLU ---

@app.route('/api/nlu/inbox', methods=['GET'])
@login_required
def api_nlu_inbox():
    """Devuelve la lista de frases no reconocidas."""
    inbox_path = 'data/nlu_inbox.json'
    if os.path.exists(inbox_path):
        with open(inbox_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/nlu/intents', methods=['GET'])
@login_required
def api_nlu_intents():
    """Devuelve la lista de intents disponibles."""
    intents_path = 'config/intents.json'
    if os.path.exists(intents_path):
        with open(intents_path, 'r') as f:
            data = json.load(f)
            return jsonify([i['name'] for i in data.get('intents', [])])
    return jsonify([])

@app.route('/api/nlu/train', methods=['POST'])
@login_required
def api_nlu_train():
    """Asigna una frase a un intent y la guarda."""
    data = request.json
    phrase = data.get('phrase')
    intent = data.get('intent')
    
    if not phrase or not intent:
        return jsonify({'success': False, 'message': 'Faltan datos'})

    try:
        # 1. Añadir a learned_intents.json
        learned_path = 'config/learned_intents.json'
        learned_data = {}
        if os.path.exists(learned_path):
            with open(learned_path, 'r') as f:
                learned_data = json.load(f)
        
        if intent not in learned_data:
            learned_data[intent] = []
        
        if phrase not in learned_data[intent]:
            learned_data[intent].append(phrase)
            
        with open(learned_path, 'w') as f:
            json.dump(learned_data, f, indent=4)
            
        # Actualizar intents.json si es necesario (opcional, lógica simple)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/nlu/train/alias', methods=['POST'])
@login_required
def api_nlu_train_alias():
    """Asigna una frase fallida a un comando específico (Alias)."""
    data = request.json
    trigger = data.get('trigger')
    command = data.get('command')
    
    if not trigger or not command:
        return jsonify({'success': False, 'message': 'Faltan datos'})

    try:
        # 1. Usar Brain para almacenar Alias
        if brain.learn_alias(trigger, command):
            
            # 2. Eliminar de Bandeja de Entrada
            inbox_path = 'data/nlu_inbox.json'
            if os.path.exists(inbox_path):
                with open(inbox_path, 'r', encoding='utf-8') as f:
                    inbox = json.load(f)
                
                # Filtrar el disparador aprendido
                new_inbox = [i for i in inbox if i['text'] != trigger]
                
                with open(inbox_path, 'w', encoding='utf-8') as f:
                    json.dump(new_inbox, f, indent=4, ensure_ascii=False)
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar alias en base de datos'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
        
        if phrase not in learned_data[intent]:
            learned_data[intent].append(phrase)
            
        with open(learned_path, 'w') as f:
            json.dump(learned_data, f, indent=4)
            
        # 2. Eliminar de la bandeja de entrada
        inbox_path = 'data/nlu_inbox.json'
        if os.path.exists(inbox_path):
            with open(inbox_path, 'r') as f:
                inbox = json.load(f)
            
            inbox = [i for i in inbox if i['text'] != phrase]
            
            with open(inbox_path, 'w') as f:
                json.dump(inbox, f, indent=4)
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
    return jsonify({'success': True})

@app.route('/api/health/status', methods=['GET'])
@login_required
def api_health_status():
    """Devuelve el estado del sistema de autocuración y últimos incidentes."""
    history_path = 'data/health_history.json'
    recent_incidents = 0
    last_event = "System Normal"
    status = "Active"
    
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                data = json.load(f)
                # Filtrar últimas 24h
                now = time.time()
                recent = [i for i in data if now - i['timestamp'] < 86400]
                recent_incidents = len(recent)
                
                if data:
                    last = data[-1]
                    last_event = f"{last['event']} on {last['target']}"
        except:
             pass
             
    return jsonify({
        'status': status,
        'recent_incidents': recent_incidents,
        'last_message': last_event
    })

# --- API DEL DASHBOARD ---

@app.route('/api/dashboard/layout', methods=['GET', 'POST'])
@login_required
def api_dashboard_layout():
    """API para guardar/cargar la disposición del dashboard."""
    layout_file = 'config/dashboard_layout.json'
    
    if request.method == 'POST':
        try:
            layout = request.json.get('layout')
            if not isinstance(layout, list):
                return jsonify({'success': False, 'message': 'Invalid format'})
                
            with open(layout_file, 'w') as f:
                json.dump(layout, f)
            return jsonify({'success': True})
        except Exception as e:
             return jsonify({'success': False, 'message': str(e)})
             
    else: # GET
        if os.path.exists(layout_file):
            try:
                with open(layout_file, 'r') as f:
                    return jsonify(json.load(f))
            except:
                return jsonify([])
        return jsonify([])

# --- API DE ARCHIVOS ---

@app.route('/api/files/list', methods=['POST'])
@login_required
def api_files_list():
    """Lista directorio."""
    path = request.json.get('path')
    if not path:
        path = os.path.expanduser('~') # Por defecto a HOME en lugar de /
    success, items = file_manager.list_directory(path)
    if success:
        return jsonify({'success': True, 'items': items})
    return jsonify({'success': False, 'message': items})

@app.route('/api/files/read', methods=['POST'])
@login_required
def api_files_read():
    """Lee archivo."""
    path = request.json.get('path')
    success, content = file_manager.read_file(path)
    if success:
        return jsonify({'success': True, 'content': content})
    return jsonify({'success': False, 'message': content})

@app.route('/api/files/save', methods=['POST'])
@login_required
def api_files_save():
    """Guarda archivo."""
    data = request.json
    success, msg = file_manager.save_file(data['path'], data['content'])
    return jsonify({'success': success, 'message': msg})

@app.route('/api/visual/content', methods=['GET'])
def api_visual_content():
    """Sirve contenido visual (imágenes, PDFs) para la interfaz facial."""
    # Seguridad: Añadir validación de ruta
    path = request.args.get('path')
    
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    # Resolver a ruta absoluta para prevenir salto de directorio
    try:
        abs_path = os.path.realpath(path)
    except Exception as e:
        app_logger.warning(f"Invalid path provided: {path}, error: {e}")
        return jsonify({'error': 'Invalid path'}), 400
    
    # Definir directorios base permitidos
    ALLOWED_DIRS = [
        os.path.expanduser('~'),  # Directorio home del usuario
        '/tmp',                   # Directorio temporal
        os.getcwd()               # Directorio de trabajo actual
    ]
    
    # Comprobar si la ruta está dentro de los directorios permitidos
    if not any(abs_path.startswith(os.path.realpath(d)) for d in ALLOWED_DIRS):
        app_logger.warning(f"Access denied - path outside allowed dirs: {abs_path}")
        return jsonify({'error': 'Access denied'}), 403
    
    if not os.path.exists(abs_path):
        return jsonify({'error': 'File not found'}), 404
        
    if not os.path.isfile(abs_path):
        return jsonify({'error': 'Path is not a file'}), 400
    
    # Servir el archivo
    try:
        return send_file(abs_path)
    except Exception as e:
        app_logger.error(f"Error serving file {abs_path}: {e}")
        return jsonify({'error': 'Error serving file'}), 500

# --- API DE CONOCIMIENTO ---

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'docs', 'brain_memory')

@app.route('/api/knowledge/upload', methods=['POST'])
@login_required
def api_knowledge_upload():
    """Sube un documento para la base de conocimientos."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
        
    if file:
        filename = file.filename
        # Asegurarse de que exista la carpeta de subidas
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        return jsonify({'success': True, 'message': 'Archivo subido a brain_memory.'})

@app.route('/api/knowledge/list_docs', methods=['GET'])
@login_required
def api_knowledge_list_docs():
    """Lista los documentos en la carpeta brain_memory."""
    # La ruta de Docs está hardcodeada en el init de KnowledgeBase a "docs" o pasada vía constructor.
    # Deberíamos usar la misma lógica.
    # Por ahora, listando directorio 'docs'.
    docs_path = os.path.join(os.getcwd(), 'docs')
    if os.path.exists(docs_path):
         # Solo listar archivos
         files = []
         for root, dirs, filenames in os.walk(docs_path):
             for f in filenames:
                 if f.endswith(('.txt', '.md', '.pdf')):
                     files.append(f)
         return jsonify(files)
    return jsonify([])

@app.route('/api/knowledge/train', methods=['POST'])
@login_required
def api_knowledge_train():
    """Dispara la re-ingesta de documentos en ChromaDB."""
    try:
        force = request.json.get('force', False)
        # Re-inicializar para asegurarse de que recoge nuevos archivos si es necesario, o solo llamar a ingest
        # knowledge_base es global
        knowledge_base.ingest_docs(force=force)
        return jsonify({'success': True, 'message': 'Entrenamiento completado.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- API DEL PROGRAMADOR ---

@app.route('/api/tasks/list', methods=['GET'])
@login_required
def api_tasks_list():
    return jsonify(scheduler_manager.get_jobs())

@app.route('/api/tasks/add', methods=['POST'])
@login_required
def api_tasks_add():
    data = request.json
    name = data.get('name')
    command = data.get('command')
    cron = data.get('cron') # "min hour day month dow"
    
    success, msg = scheduler_manager.add_bash_job(name, command, cron)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/tasks/delete', methods=['POST'])
@login_required
def api_tasks_delete():
    data = request.json
    job_id = data.get('id')
    success, msg = scheduler_manager.delete_job(job_id)
    return jsonify({'success': success, 'message': msg})


@app.route('/api/knowledge/delete_doc', methods=['POST'])
@login_required
def api_knowledge_delete_doc():
    """Borra un documento."""
    filename = request.json.get('filename')
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'File not found'})

@app.route('/api/config/get', methods=['GET'])
@login_required
def api_config_get():
    """Devuelve la configuración completa y listas de modelos disponibles."""
    config = config_manager.get_all() or {}
    
    # List available voices
    voices_dir = os.path.join(os.getcwd(), 'piper', 'voices')
    available_voices = []
    if os.path.exists(voices_dir):
        for f in os.listdir(voices_dir):
            if f.endswith('.onnx'):
                available_voices.append(f)
    
    # List available AI models (GGUF)
    models_dir = os.path.join(os.getcwd(), 'models')
    available_models = []
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            if f.endswith('.gguf'):
                available_models.append(f)
                
    return jsonify({
        'config': config,
        'voices': available_voices,
        'models': available_models
    })

def run_server():
    """Inicia el servidor Flask con SocketIO."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    web_config = config_manager.get('web_admin', {})
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug_mode = web_config.get('debug', False)
    
    # Comprobar Certificados SSL
    cert_dir = os.path.join(os.getcwd(), 'config', 'certs')
    cert_file = os.path.join(cert_dir, 'neo.crt')
    key_file = os.path.join(cert_dir, 'neo.key')
    
    ssl_context = None
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f" HTTPS Enabled. Using certs from {cert_dir}")
        # ssl_context = (cert_file, key_file) # Desactivado para compatibilidad con Kiosco
        ssl_context = None 
    else:
        print("[WARN] HTTPS Disabled. Certs not found in config/certs/")
        
    print(f"[START] Neo Web Admin running on https://{host}:{port}" if ssl_context else f"[START] Neo Web Admin running on http://{host}:{port}")
    
    # FORZAR DEBUG=FALSE para evitar el fallback de Werkzeug que causa 'write() before start_response'
    # NOTA: eventlet no soporta 'ssl_context' (usa keyfile/certfile), así que lo eliminamos.
    # SSL está actualmente desactivado en el código superior (ssl_context=None).
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False, log_output=False, allow_unsafe_werkzeug=True)
