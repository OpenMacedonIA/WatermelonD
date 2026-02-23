"""
Intent Matcher para categoría SECURE
Sistema de comparación de intents con extracción de contexto
Se activa cuando el Router categoriza un comando como 'secure'
"""

import re
import os
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("SecureIntentMatcher")


class SecureIntentMatcher:
    """
    Comparador de intents para comandos de seguridad.
    Extrae contexto (IPs, archivos, puertos) y genera comandos.
    """
    
    def __init__(self):
        self.intents = self._load_intents()
        logger.info(f"SecureIntentMatcher inicializado con {len(self.intents)} intents")
    
    def _load_intents(self) -> List[Dict]:
        """Define los intents de seguridad con patrones y plantillas de comandos."""
        return [
            # ============ CLAMAV ============
            {
                'triggers': [
                    'escanea descargas', 'busca virus en descargas', 'analiza descargas',
                    'escanea downloads', 'revisa descargas', 'chequea descargas',
                    'mira si hay virus en descargas', 'analiza mis descargas',
                    'busca malware en descargas', 'escanea la carpeta de descargas',
                    'revisa downloads', 'escanea archivos descargados',
                    'analiza archivos en downloads', 'busca virus downloads',
                    'hay virus en descargas', 'chequea downloads por virus',
                    'escanea todo en descargas', 'analiza carpeta descargas'
                ],
                'cmd_template': 'clamscan --infected ~/Downloads/',
                'requires_context': False,
                'category': 'clamav'
            },
            {
                'triggers': [
                    'escanea el archivo', 'busca virus en archivo', 'analiza archivo',
                    'escanea archivo', 'revisa archivo', 'chequea archivo',
                    'busca virus en el archivo', 'analiza el fichero',
                    'escanea fichero', 'revisa el archivo', 'mira el archivo',
                    'escanea ese archivo', 'analiza ese fichero',
                    'busca malware en archivo', 'chequea el archivo'
                ],
                'cmd_template': 'clamscan {file}',
                'requires_context': True,
                'context_extractors': {'file': r'archivo\s+(\S+)|fichero\s+(\S+)|ese\s+(\S+)'},
                'category': 'clamav'
            },
            {
                'triggers': [
                    'actualiza firmas', 'actualiza antivirus', 'update virus',
                    'actualiza el antivirus', 'actualiza las firmas de virus',
                    'refresca firmas', 'actualiza base de datos de virus',
                    'update antivirus', 'actualiza clamav', 'refresca antivirus',
                    'actualiza signatures', 'actualiza definiciones',
                    'actualiza base de malware', 'refresca base de virus',
                    'update firmas', 'actualiza firmas de malware'
                ],
                'cmd_template': 'sudo freshclam',
                'requires_context': False,
                'category': 'clamav'
            },
            {
                'triggers': [
                    'estado del antivirus', 'estado de clamav', 'status antivirus',
                    'como esta el antivirus', 'estado clamav', 'status clamav',
                    'esta activo clamav', 'esta corriendo el antivirus',
                    'funciona el antivirus', 'estado del daemon de clamav'
                ],
                'cmd_template': 'systemctl status clamav-daemon',
                'requires_context': False,
                'category': 'clamav'
            },
            
            # ============ FAIL2BAN ============
            {
                'triggers': [
                    'estado de fail2ban', 'muestra fail2ban', 'status fail2ban',
                    'como esta fail2ban', 'estado fail2ban', 'muestra estado fail2ban',
                    'esta activo fail2ban', 'funciona fail2ban',
                    'esta corriendo fail2ban', 'status de fail2ban'
                ],
                'cmd_template': 'sudo fail2ban-client status',
                'requires_context': False,
                'category': 'fail2ban'
            },
            {
                'triggers': [
                    'ips bloqueadas', 'muestra ips bloqueadas', 'ips baneadas',
                    'lista ips bloqueadas', 'que ips estan bloqueadas',
                    'muestra ips baneadas', 'cuantas ips bloqueadas',
                    'lista bans', 'ips en ban', 'muestra bans',
                    'que ips baneaste', 'enseñame ips bloqueadas',
                    'lista ips baneadas en ssh', 'cuantas ips baneadas hay'
                ],
                'cmd_template': 'sudo fail2ban-client status sshd',
                'requires_context': False,
                'category': 'fail2ban'
            },
            {
                'triggers': [
                    'desbloquea ip', 'desbanea ip', 'quita ban de ip',
                    'desbloquea la ip', 'quita el ban', 'desbanea la ip',
                    'unban ip', 'saca ip del ban', 'libera ip',
                    'quita bloqueo de ip', 'desbloquea', 'unban',
                    'saca del ban', 'libera la ip', 'quita ban ip'
                ],
                'cmd_template': 'sudo fail2ban-client set sshd unbanip {ip}',
                'requires_context': True,
                'context_extractors': {'ip': r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'},
                'category': 'fail2ban'
            },
            {
                'triggers': [
                    'banea ip', 'bloquea ip', 'banea la ip',
                    'bloquea la ip', 'ban ip', 'pon en ban',
                    'banea', 'bloquea', 'mete en ban',
                    'pon ban a ip', 'bloquea acceso de ip',
                    'banea esta ip', 'bloquea esta ip'
                ],
                'cmd_template': 'sudo fail2ban-client set sshd banip {ip}',
                'requires_context': True,
                'context_extractors': {'ip': r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'},
                'category': 'fail2ban'
            },
            
            # ============ LOGS DE SEGURIDAD ============
            {
                'triggers': [
                    'intentos fallidos', 'logins fallidos', 'failed password',
                    'muestra intentos fallidos', 'accesos fallidos',
                    'lista intentos fallidos', 'quien intento entrar',
                    'muestra failed password', 'lista logins fallidos',
                    'intentos de login fallidos', 'contraseñas incorrectas',
                    'failed logins', 'errores de login', 'accesos denegados',
                    'intentos de acceso fallidos', 'logins rechazados'
                ],
                'cmd_template': 'sudo grep "Failed password" /var/log/auth.log | tail -20',
                'requires_context': False,
                'category': 'logs'
            },
            {
                'triggers': [
                    'logins exitosos', 'accesos ssh', 'conexiones exitosas',
                    'muestra logins exitosos', 'accesos correctos',
                    'quien se conecto', 'lista accesos ssh', 'conexiones ssh',
                    'logins aceptados', 'accesos aceptados', 'quien entro',
                    'muestra conexiones ssh', 'lista logins correctos',
                    'accesos ssh exitosos', 'conexiones ssh exitosas'
                ],
                'cmd_template': 'sudo grep "Accepted" /var/log/auth.log | tail -10',
                'requires_context': False,
                'category': 'logs'
            },
            {
                'triggers': [
                    'log de autenticacion', 'auth log', 'logs de auth',
                    'muestra auth log', 'ver log de autenticacion',
                    'muestra log auth', 'logs de autenticacion',
                    'ver auth log', 'muestra logs auth', 'log auth',
                    'ver logs de autenticacion', 'muestra autenticacion'
                ],
                'cmd_template': 'sudo tail -50 /var/log/auth.log',
                'requires_context': False,
                'category': 'logs'
            },
            
            # ============ USUARIOS Y PRIVILEGIOS ============
            {
                'triggers': [
                    'usuarios con sudo', 'quien tiene sudo', 'lista sudo',
                    'muestra usuarios con sudo', 'que usuarios tienen sudo',
                    'lista usuarios sudo', 'usuarios que pueden hacer sudo',
                    'quien puede sudo', 'lista privilegios sudo',
                    'usuarios con privilegios', 'quien tiene permisos sudo',
                    'muestra sudo users', 'lista sudoers'
                ],
                'cmd_template': 'grep -Po "^sudo.+:\\K.*$" /etc/group',
                'requires_context': False,
                'category': 'users'
            },
            {
                'triggers': [
                    'archivos suid', 'busca suid', 'encuentra suid',
                    'lista archivos suid', 'muestra suid', 'archivos con suid',
                    'busca archivos suid', 'encuentra archivos suid',
                    'lista suid', 'archivos con bit suid',
                    'busca bit suid', 'encuentra bit suid'
                ],
                'cmd_template': 'find / -perm -4000 -type f 2>/dev/null',
                'requires_context': False,
                'category': 'users'
            },
            {
                'triggers': [
                    'ultimo login', 'ultimos accesos', 'lastlog',
                    'muestra ultimo login', 'ultimos logins',
                    'ultimo acceso de usuarios', 'cuando se logueo',
                    'ultima vez que entraron', 'muestra lastlog',
                    'lista ultimos accesos', 'ultimo login usuarios'
                ],
                'cmd_template': 'lastlog',
                'requires_context': False,
                'category': 'users'
            },
            
            # ============ AUDITORÍA ============
            {
                'triggers': [
                    'auditoria del sistema', 'escaneo de seguridad', 'ejecuta lynis',
                    'auditoria de seguridad', 'escanea seguridad',
                    'ejecuta auditoria', 'corre lynis', 'audit sistema',
                    'revisa seguridad del sistema', 'analiza seguridad',
                    'escaneo lynis', 'auditoria lynis', 'security audit',
                    'analiza vulnerabilidades', 'busca vulnerabilidades'
                ],
                'cmd_template': 'sudo lynis audit system --quick',
                'requires_context': False,
                'category': 'audit'
            },
            {
                'triggers': [
                    'busca rootkits', 'escanea rootkits', 'chkrootkit',
                    'escanea por rootkits', 'busca rootkit', 'detecta rootkits',
                    'ejecuta chkrootkit', 'corre chkrootkit', 'analiza rootkits',
                    'revisa rootkits', 'hay rootkits', 'detecta rootkit'
                ],
                'cmd_template': 'sudo chkrootkit -q',
                'requires_context': False,
                'category': 'audit'
            },
            
            # ============ MONITOREO ============
            {
                'triggers': [
                    'procesos sospechosos', 'procesos en tmp', 'busca malware',
                    'muestra procesos sospechosos', 'hay procesos raros',
                    'busca procesos sospechosos', 'procesos maliciosos',
                    'detecta malware', 'procesos extraños',
                    'busca netcat', 'procesos en temporal'
                ],
                'cmd_template': 'ps aux | grep -iE "nc|ncat|netcat|/tmp"',
                'requires_context': False,
                'category': 'monitor'
            },
            {
                'triggers': [
                    'conexiones sospechosas', 'conexiones establecidas',
                    'muestra conexiones', 'lista conexiones activas',
                    'conexiones activas', 'que conexiones hay',
                    'muestra conexiones establecidas', 'conexiones tcp',
                    'lista conexiones tcp', 'conexiones de red activas'
                ],
                'cmd_template': 'sudo netstat -ntp | grep ESTABLISHED',
                'requires_context': False,
                'category': 'monitor'
            },
            
            # ============ HARDENING ============
            {
                'triggers': [
                    'configuracion ssh', 'revisa ssh', 'config de ssh',
                    'muestra config ssh', 'configuracion de ssh',
                    'ver config ssh', 'ssh config', 'parametros ssh',
                    'muestra configuracion ssh', 'settings ssh'
                ],
                'cmd_template': 'sudo sshd -T',
                'requires_context': False,
                'category': 'hardening'
            },
            {
                'triggers': [
                    'valida ssh', 'testea ssh', 'test ssh',
                    'valida config ssh', 'comprueba ssh',
                    'verifica ssh', 'chequea ssh', 'test config ssh'
                ],
                'cmd_template': 'sudo sshd -t',
                'requires_context': False,
                'category': 'hardening'
            },
            
            # ============ FUNCIONES PYTHON ============
            {
                'triggers': [
                    'estado de seguridad', 'reporte de seguridad', 'como esta la seguridad',
                    'status de seguridad', 'estado seguridad', 'reporte seguridad',
                    'que tal la seguridad', 'muestra estado de seguridad',
                    'security status', 'muestra seguridad', 'status seguridad'
                ],
                'cmd_template': 'SecuritySkill.security_status()',
                'requires_context': False,
                'category': 'python',
                'is_python': True
            },
            {
                'triggers': [
                    'lista cuarentena', 'archivos en cuarentena', 'ver cuarentena',
                    'muestra cuarentena', 'que hay en cuarentena',
                    'lista archivos en cuarentena', 'archivos cuarentena',
                    'muestra archivos infectados', 'ver archivos cuarentena',
                    'lista quarantine', 'muestra archivos en cuarentena'
                ],
                'cmd_template': 'SecuritySkill.list_quarantine()',
                'requires_context': False,
                'category': 'python',
                'is_python': True
            }
        ]
    
    def extract_context(self, command: str, extractors: Dict[str, str]) -> Dict[str, str]:
        """
        Extrae contexto del comando usando regex.
        
        Args:
            command: Comando en lenguaje natural
            extractors: Dict de {nombre_variable: patron_regex}
        
        Devuelve:
            Dict con valores extraídos
        """
        context = {}
        
        for var_name, pattern in extractors.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                # Tomar el primer grupo que no sea None
                value = next((g for g in match.groups() if g), None)
                if value:
                    context[var_name] = value
        
        return context
    
    def match_intent(self, command: str) -> Optional[Tuple[str, Dict, str]]:
        """
        Encuentra el intent que mejor coincide con el comando.
        
        Args:
            command: Comando en lenguaje natural
        
        Devuelve:
            (cmd, context, category) o None si no hay match
        """
        command_lower = command.lower()
        
        for intent in self.intents:
            # Verificar triggers
            for trigger in intent['triggers']:
                if trigger in command_lower:
                    context = {}
                    
                    # Extraer contexto si es necesario
                    if intent.get('requires_context'):
                        extractors = intent.get('context_extractors', {})
                        context = self.extract_context(command, extractors)
                        
                        # Si requiere contexto pero no se extrajo, saltar
                        if not context:
                            logger.debug(f"Intent '{trigger}' requiere contexto pero no se extrajo")
                            continue
                    
                    # Generar comando
                    cmd_template = intent['cmd_template']
                    
                    try:
                        if context:
                            # Expandir paths si es archivo
                            if 'file' in context:
                                file_path = context['file']
                                # Si no es ruta absoluta, buscar en descargas
                                if not file_path.startswith('/'):
                                    file_path = os.path.join(os.path.expanduser('~/Downloads'), file_path)
                                context['file'] = file_path
                            
                            cmd = cmd_template.format(**context)
                        else:
                            cmd = cmd_template
                        
                        category = intent.get('category', 'unknown')
                        is_python = intent.get('is_python', False)
                        
                        logger.info(f"Intent match: '{trigger}' → {cmd}")
                        
                        return cmd, context, category, is_python
                        
                    except KeyError as e:
                        logger.error(f"Error formateando comando: falta variable {e}")
                        continue
        
        return None
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de los intents cargados."""
        categories = {}
        for intent in self.intents:
            cat = intent.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_intents': len(self.intents),
            'categories': categories,
            'with_context': len([i for i in self.intents if i.get('requires_context')]),
            'python_functions': len([i for i in self.intents if i.get('is_python')])
        }
