# Documentación de Seguridad Integral del Proyecto WatermelonD (WatermelonD)

Esta guía detalla exhaustivamente las medidas de seguridad implementadas en el sistema WatermelonD, abarcando desde la protección a nivel de aplicación web hasta el endurecimiento (hardening) del sistema operativo subyacente.

---

## Tabla de Contenidos

1. [Introducción y Filosofía de Seguridad](#1-introducción-y-filosofía-de-seguridad)
2. [Seguridad en la Aplicación Web (WatermelonD Web Admin)](#2-seguridad-en-la-aplicación-web-neo-web-admin)
 * 2.1. Autenticación Robusta y Hashing
 * 2.2. Encriptación HTTPS (SSL/TLS)
 * 2.3. Protección CSRF
 * 2.4. Limitación de Intentos (Rate Limiting)
 * 2.5. Cabeceras de Seguridad HTTP
3. [Seguridad del Sistema Operativo](#3-seguridad-del-sistema-operativo)
 * 3.1. Firewall (UFW)
 * 3.2. Prevención de Intrusiones (Fail2Ban)
 * 3.3. Permisos de Archivos y Directorios
4. [Herramientas de Seguridad](#4-herramientas-de-seguridad)
 * 4.1. `password_helper.py`
 * 4.2. `secure_system.sh`
5. [Procedimientos de Mantenimiento](#5-procedimientos-de-mantenimiento)
6. [Resolución de Problemas Comunes](#6-resolución-de-problemas-comunes)

---

## 1. Introducción y Filosofía de Seguridad

La seguridad en WatermelonD no es una característica añadida, sino un componente fundamental dada la naturaleza del asistente: un dispositivo siempre activo, con capacidad de escucha (micrófono), visión (cámara) y control sobre otros dispositivos IoT.

Nuestro enfoque de seguridad se basa en **"Defensa en Profundidad"**:
* **Capa Web**: Protege la interfaz de administración contra accesos no autorizados y ataques comunes.
* **Capa de Red**: Filtra el tráfico no deseado antes de que llegue a las aplicaciones.
* **Capa de Sistema**: Minimiza el daño potencial restringiendo permisos y monitoreando actividades sospechosas.

---

## 2. Seguridad en la Aplicación Web (WatermelonD Web Admin)

El módulo `web_admin.py` ha sido fortificado significativamente para proteger el acceso al panel de control.

### 2.1. Autenticación Robusta y Hashing

Anteriormente, las credenciales se almacenaban en texto plano en `config.json`, lo cual representaba un riesgo crítico si el archivo era comprometido.

**Implementación Actual:**
* **Hashing**: Utilizamos `werkzeug.security` con algoritmos modernos (PBKDF2/SHA256) para almacenar solo el hash de la contraseña, nunca la contraseña real.
* **Migración Automática**: Al arrancar, el sistema detecta si la contraseña en `config.json` es texto plano (legacy) y la convierte automáticamente a un hash seguro.
* **CLI Helper**: Se introduce `resources/tools/password_helper.py` para establecer contraseñas de forma segura desde la terminal sin editar archivos manualmente.

**Ejemplo de Configuración Segura (`config.json`):**
```json
{
 "admin_user": "admin",
 "admin_pass": "pbkdf2:sha256:600000$Xyz...$Abc..."
}
```

### 2.2. Encriptación HTTPS (SSL/TLS)

Para evitar la interceptación de datos (Sniffing) en la red local, especialmente durante el inicio de sesión, se fuerza el uso de HTTPS.

* **Generación de Certificados**: El instalador (`install.sh`) utiliza `openssl` para generar automáticamente un par de claves:
 * `config/certs/neo.key`: Clave privada (Permisos 600).
 * `config/certs/neo.crt`: Certificado autofirmado (Permisos 644).
* **Activación**: `web_admin.py` detecta la presencia de estos archivos y, si existen, levanta el servidor Flask con contexto SSL (`ssl_context`).
* **Navegadores**: Al ser un certificado autofirmado, los navegadores mostrarán una advertencia de "Sitio no seguro". Esto es normal en redes locales. El usuario debe aceptar el riesgo o importar `neo.crt` como autoridad de certificación de confianza en su navegador.

### 2.3. Protección CSRF (Cross-Site Request Forgery)

Se ha implementado `Flask-WTF` con `CSRFProtect` para blindar la aplicación contra ataques donde un sitio malicioso fuerza al navegador del usuario (ya autenticado) a ejecutar acciones en WatermelonD.

* **Token CSRF Global**: Se inyecta un token en todas las plantillas HTML a través de una etiqueta meta:
 ```html
 <meta name="csrf-token" content="{{ csrf_token() }}">
 ```
* **Intercepción AJAX**: Un script en `base.html` intercepta automáticamente todas las peticiones `fetch` (POST, PUT, DELETE) y les añade la cabecera `X-CSRFToken`. Esto asegura que las acciones dinámicas (como borrar un archivo o controlar un servicio) estén protegidas sin modificar cada llamada JavaScript individualmente.
* **Formularios Estándar**: Los formularios HTML clásicos incluyen un campo oculto `<input type="hidden" name="csrf_token" ...>`.

### 2.4. Limitación de Intentos (Rate Limiting)

Para mitigar ataques de fuerza bruta al login:
* Se utiliza un decorador `@rate_limit_login` en la ruta `/login`.
* **Límite**: 5 intentos fallidos por dirección IP por minuto.
* Si se excede, el servidor devuelve un error 429 (Too Many Requests) y bloquea temporalmente esa IP.

### 2.5. Cabeceras de Seguridad HTTP

Cada respuesta del servidor incluye cabeceras para endurecer el comportamiento del navegador:
* `X-Frame-Options: SAMEORIGIN`: Previene ataques de Clickjacking impidiendo que la web sea incrustada en iframes de otros dominios.
* `X-Content-Type-Options: nosniff`: Evita que el navegador mime-sniffing tipos de archivos incorrectos (riesgo XSS).
* `Strict-Transport-Security` (HSTS): Fuerza al navegador a usar HTTPS en futuras visitas.

---

## 3. Seguridad del Sistema Operativo

Además de proteger la aplicación, endurecemos el sistema operativo anfitrión (Debian/Fedora) mediante el script `secure_system.sh`.

### 3.1. Firewall (UFW)

Usamos **UFW (Uncomplicated Firewall)** para cerrar el dispositivo al mundo exterior, creando una lista blanca estricta.

**Política por Defecto:**
* Entrante (`Incoming`): **DENEGAR** (Bloquea todo por defecto).
* Saliente (`Outgoing`): **PERMITIR** (WatermelonD puede acceder a internet para APIs, actualizaciones, etc.).

**Reglas de Permitir (Allow):**
1. **Puerto 22 (SSH)**: Esencial para la administración remota. *Riesgo*: Si se bloquea este puerto y UFW se activa, perderá acceso remoto.
2. **Puerto 5000 (TCP)**: Interfaz web de WatermelonD.

**Comandos Útiles:**
* `sudo ufw status verbose`: Ver estado actual.
* `sudo ufw enable`: Activar firewall.
* `sudo ufw disable`: Desactivar (en caso de problemas).

### 3.2. Prevención de Intrusiones (Fail2Ban)

Fail2Ban es un servicio que monitoriza los logs del sistema (`/var/log/auth.log`) buscando patrones de ataques de fuerza bruta contra SSH.

**Configuración (`/etc/fail2ban/jail.local`):**
* **MaxRetry**: 3 intentos fallidos.
* **FindTime**: 600 segundos (10 minutos). Si fallas 3 veces en 10 minutos...
* **BanTime**: 3600 segundos (1 hora). La IP atacante es bloqueada a nivel de Firewall (iptables) durante una hora.

Esto hace inviable intentar adivinar contraseñas mediante fuerza bruta, ya que el atacante pasará la mayor parte del tiempo baneado.

### 3.3. Permisos de Archivos y Directorios

El principio de "mínimo privilegio" se aplica a los archivos sensibles del proyecto.

* **Configuración y Credenciales**:
 * Directorio: `config/`
 * Archivos: `config.json`, `skills.json`, `*.json`
 * **Permiso**: `600` (Solo lectura/escritura para el propietario).
 * **Propietario**: El usuario que ejecuta el servicio WatermelonD (ej: `pi`, `usuario`).
 * **Efecto**: Otros usuarios del sistema (invitados o comprometidos) no pueden leer las claves API o hashes de contraseñas.

* **Base de Datos**:
 * Directorio: `database/`
 * Archivos: `BrainNut.db` (y WAL/SHM)
 * **Permiso**: `600`
 * **Efecto**: Protege el historial de conversaciones y datos de memoria a largo plazo.

* **Certificados SSL**:
 * Directorio: `config/certs/`
 * Archivos: `neo.key`
 * **Permiso**: `600` Estricto. Nadie más debe leer la clave privada.

---

## 4. Herramientas de Seguridad

El proyecto incluye scripts específicos para facilitar la gestión de seguridad.

### 4.1. `resources/tools/password_helper.py`

Herramienta de línea de comandos para gestionar el usuario administrador sin editar JSONs a mano.

**Uso:**
```bash
# Modo interactivo (Pide contraseña oculta)
python3 resources/tools/password_helper.py --user admin

# Modo directo (Útil para scripts, cuidado con el historial de bash)
python3 resources/tools/password_helper.py --user admin --password "MiNuevaClaveSegura"
```

**Funcionamiento:**
1. Carga `config/config.json`.
2. Genera un hash seguro de la contraseña.
3. Guarda el hash en `config.json` preservando el resto de la configuración.

### 4.2. `resources/tools/secure_system.sh`

Script "One-Click Hardening". Se puede ejecutar tras la instalación o en cualquier momento.

**Acciones que realiza:**
1. Instala dependencias: `ufw`, `fail2ban`.
2. Configura reglas de UFW (SSH, Web).
3. Pregunta antes de activar UFW (para evitar bloqueos accidentales).
4. Configura `jail.local` de Fail2Ban para SSH.
5. Aplica `chmod 600` recursivo a carpetas sensibles (`config/`, `database/`).

**Uso:**
```bash
sudo ./resources/tools/secure_system.sh
```

---

## 5. Procedimientos de Mantenimiento

### Cambio de Contraseña de Administrador
1. **Vía Web**: Ir a `Ajustes` > `Seguridad`. Introducir la nueva contraseña. El sistema gestionará el hash.
2. **Vía Terminal** (si olvidó la clave):
 ```bash
 cd ~/WatermelonD
 source venv/bin/activate
 python3 resources/tools/password_helper.py --user admin
# Siga las instrucciones
 sudo systemctl restart neo.service --user
 ```

### Rotación de Certificados SSL
Los certificados autofirmados caducan (configurados a 10 años por defecto en el instalador, pero es buena práctica saber regenerarlos).

```bash
# Borrar certificados antiguos
rm config/certs/neo.*

# Regenerar (usando openssl directamente o relanzando install.sh que detectará que faltan)
openssl req -x509 -newkey rsa:4096 -keyout config/certs/neo.key -out config/certs/neo.crt -days 3650 -nodes -subj "/CN=$(hostname)"
chmod 600 config/certs/neo.key
systemctl restart neo.service --user
```

### Verificación de Intrusos
Revisar regularmente los intentos de acceso bloqueados por Fail2Ban:
```bash
sudo cat /var/log/fail2ban.log | grep Ban
```

---

## 6. Resolución de Problemas Comunes

### "No puedo acceder a la web, el navegador dice conexión rechazada"
* Verifique si el servicio está corriendo: `systemctl --user status neo.service`.
* Verifique si UFW está bloqueando el puerto 5000: `sudo ufw status`. Si falta la regla, añádala: `sudo ufw allow 5000/tcp`.

### "No puedo acceder por SSH"
* Si UFW está activo y no permitió el puerto 22, necesitará acceso físico (teclado/pantalla) al dispositivo.
* Ejecute: `sudo ufw allow 22/tcp`.

### "Advertencia de sitio no seguro en el navegador"
* Esto es esperado con SSL autofirmado.
* **Solución**: Haga clic en "Avanzado" -> "Continuar a (sitio)".
* **Solución Permanente**: Importe `config/certs/neo.crt` en el almacén de certificados de su SO o navegador.

### "Error 400 Bad Request: The CSRF token is missing"
* Ocurre si intenta hacer una petición POST (ej: Curl, Postman) sin incluir el token o la cabecera `X-CSRFToken`.
* Asegúrese de usar la interfaz web oficial o, si desarrolla un script, obtenga primero el token de una petición GET y úselo.

### "Permission Denied" al editar config.json
* Debido al hardening, los permisos son estrictos.
* Asegúrese de ser el usuario propietario del archivo.
* Si necesita editarlo como otro usuario, use `sudo`.

---

**Resumen de Seguridad:**
Este conjunto de medidas transforma a WatermelonD de un prototipo de desarrollo a un sistema de producción robusto, capaz de resistir ataques básicos y proteger la privacidad de los datos del usuario en entornos domésticos y semiprofesionales.
