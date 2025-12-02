from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from flask_socketio import SocketIO, emit
import functools
import os
import json
import subprocess
from modules.sysadmin import SysAdminManager
from modules.database import DatabaseManager
from modules.config_manager import ConfigManager
from modules.ssh_manager import SSHManager
from modules.ssh_manager import SSHManager
from modules.file_manager import FileManager
from modules.wifi_manager import WifiManager
from modules.dashboard_data import DashboardDataManager

app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')

config_manager = ConfigManager()

# Persistent Secret Key
secret_key = config_manager.get('secret_key')
if not secret_key:
    secret_key = os.urandom(24).hex()
    config_manager.set('secret_key', secret_key)

app.secret_key = secret_key

# Initialize SocketIO
# Usamos threading para evitar conflictos con PyAudio/Threads de NeoCore
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

sys_admin = SysAdminManager()
db = DatabaseManager()
ssh_manager = SSHManager()
ssh_manager = SSHManager()
file_manager = FileManager()
wifi_manager = WifiManager()
dashboard_manager = DashboardDataManager(config_manager)

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
def login():
    """Página de inicio de sesión."""
    error = None
    if request.method == 'POST':
        user = config_manager.get('admin_user', 'admin')
        password = config_manager.get('admin_pass', 'admin')
        
        if request.form['username'] != user or request.form['password'] != password:
            error = 'Credenciales inválidas. Inténtalo de nuevo.'
        else:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- PAGES ---

@app.route('/dashboard')
@login_required
def dashboard():
    """Renderiza el dashboard principal."""
    return render_template('dashboard.html', page='dashboard')

@app.route('/services')
@login_required
def services():
    """Renderiza la página de gestión de servicios."""
    return render_template('services.html', page='services')

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

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Renderiza y procesa la página de configuración."""
    config = config_manager.get_all()
    
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

    if request.method == 'POST':
        config_manager.set('admin_user', request.form['username'])
        config_manager.set('admin_pass', request.form['password'])
        config_manager.set('wake_word', request.form['wake_word'])
        config_manager.set('neo_ssh_enabled', 'neo_ssh_enabled' in request.form)
        
        # Handle AI Model
        selected_model = request.form.get('ai_model')
        if selected_model:
            full_model_path = os.path.join(models_dir, selected_model)
            config_manager.set('ai_model_path', full_model_path)

        # Handle TTS Model
        selected_voice = request.form.get('tts_model')
        if selected_voice:
            full_path = os.path.join(voices_dir, selected_voice)
            current_tts = config.get('tts', {})
            current_tts['piper_model'] = full_path
            config_manager.set('tts', current_tts)

        flash('Configuración guardada correctamente. Reinicia para aplicar cambios de IA.', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', page='settings', config=config, voices=available_voices, models=available_models)

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
    """API para reiniciar el sistema (requiere sudo)."""
    try:
        subprocess.Popen(['sudo', 'reboot'])
        return jsonify({'status': 'success', 'message': 'Reiniciando sistema...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
        # Get last 50 lines of ollama logs
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
                    content = f.read()[-10000:] # Last 10k chars
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

@app.route('/api/services', methods=['GET'])
@login_required
def api_services():
    """API que devuelve el estado de los servicios."""
    return jsonify(sys_admin.get_services())

@app.route('/api/services/control', methods=['POST'])
@login_required
def api_control_service():
    """API para controlar servicios (start/stop/restart)."""
    data = request.json
    success, msg = sys_admin.control_service(data.get('name'), data.get('action'))
    return jsonify({'success': success, 'message': msg})

@app.route('/api/network', methods=['GET'])
@login_required
def api_network():
    """API que devuelve información de red."""
    return jsonify(sys_admin.get_network_info())

@app.route('/api/network/speedtest', methods=['POST'])
@login_required
def api_network_speedtest():
    """API para ejecutar test de velocidad."""
    return jsonify(sys_admin.run_speedtest())

@app.route('/api/wifi/scan', methods=['GET'])
@login_required
def api_wifi_scan():
    """API para escanear redes WiFi."""
    networks = wifi_manager.scan()
    return jsonify(networks)

@app.route('/api/wifi/connect', methods=['POST'])
@login_required
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
def api_terminal():
    """API para ejecutar comandos de terminal con estado (cwd)."""
    cmd = request.json.get('command')
    
    # Inicializar CWD si no existe
    if 'cwd' not in session:
        session['cwd'] = os.path.expanduser('~')

    # Seguridad básica
    if 'nano' in cmd or 'vim' in cmd or 'top' in cmd:
        return jsonify({'success': False, 'output': 'Comandos interactivos no soportados.', 'cwd': session['cwd']})
    
    # Manejo especial para 'cd'
    if cmd.strip().startswith('cd '):
        target_dir = cmd.strip()[3:].strip()
        # Resolver ruta relativa
        new_path = os.path.abspath(os.path.join(session['cwd'], target_dir))
        
        if os.path.isdir(new_path):
            session['cwd'] = new_path
            return jsonify({'success': True, 'output': '', 'cwd': session['cwd']})
        else:
            return jsonify({'success': False, 'output': f"cd: {target_dir}: No such file or directory", 'cwd': session['cwd']})
    
    # Ejecutar comando normal en el CWD actual
    success, output = sys_admin.run_command(cmd, cwd=session['cwd'])
    return jsonify({'success': success, 'output': output, 'cwd': session['cwd']})

@app.route('/api/terminal/complete', methods=['POST'])
@login_required
def api_terminal_complete():
    """API para autocompletado de archivos (Tab)."""
    data = request.json
    full_command = data.get('command', '')
    
    if 'cwd' not in session:
        session['cwd'] = os.path.expanduser('~')
    
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
        
    matches = sys_admin.get_file_completions(partial, session['cwd'])
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
        'net_restart': 'sudo systemctl restart networking'
    }
    
    # Detectar Fedora para comandos diferentes
    if os.path.exists('/etc/fedora-release'):
        commands['update'] = 'sudo dnf update -y'
        commands['clean'] = 'sudo dnf clean all'

    if action_id in commands:
        success, output = sys_admin.run_command(commands[action_id])
        return jsonify({'success': success, 'output': output})
    
    return jsonify({'success': False, 'output': 'Acción desconocida'})

# --- SSH API ---

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

# --- SKILLS API ---

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
        # Load, modify, save
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

# --- NLU TRAINING API ---

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
        # 1. Add to learned_intents.json
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
            
        # 2. Remove from inbox
        inbox_path = 'data/nlu_inbox.json'
        if os.path.exists(inbox_path):
            with open(inbox_path, 'r') as f:
                inbox = json.load(f)
            
            inbox = [i for i in inbox if i['text'] != phrase]
            
            with open(inbox_path, 'w') as f:
                json.dump(inbox, f, indent=4)
                
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- FILES API ---

@app.route('/api/files/list', methods=['POST'])
@login_required
def api_files_list():
    """Lista directorio."""
    path = request.json.get('path', '/')
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
    # No requiere login estricto para que el frontend (ojos) pueda cargarlo, 
    # pero idealmente debería estar protegido o ser local.
    # Asumimos que la petición viene de localhost o red confiable.
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return "File not found", 404
        
    # Seguridad básica: evitar ../.. fuera de home si es posible, 
    # pero el asistente debe poder mostrar cualquier cosa.
    return send_file(path)

def run_server():
    """Inicia el servidor Flask con SocketIO."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    # Usamos socketio.run en lugar de app.run
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
