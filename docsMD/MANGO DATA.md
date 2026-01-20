# MANGO DATA: Documentación del Dataset de Entrenamiento
## 1. Resumen Ejecutivo

MANGO DATA es un conjunto de datos (dataset) curado manualmente y diseñado para el ajuste fino (fine-tuning) de Modelos de Lenguaje (LLMs). El objetivo es especializar al modelo en Administración de Sistemas Linux, abarcando desde operaciones básicas hasta ingeniería DevOps avanzada, gestión de redes y soporte técnico en lenguaje natural.

El dataset supera las 2.000 instrucciones de alta calidad, estructuradas en pares instrucción -> comando.
## 2. Arquitectura de los Datos

Los datos se almacenan en formato JSONL (JSON Lines), donde cada línea representa un objeto de entrenamiento independiente.
Estructura de los datos: 
```json
{
 "instruction": "Descripción en lenguaje natural (Input)",
 "cmd": "Comando de Bash ejecutable (Output)"
}
```
**Estrategia de Archivos**

Para mantener la modularidad y facilitar la depuración, el dataset se ha dividido en dos ficheros lógicos:

* **gold_commands.jsonl**: Contiene la base de conocimiento técnica, académica y formal.
* **bro_commands.jsonl**: Contiene variaciones coloquiales, jerga técnica (slang) y lenguaje natural desestructurado.

## 3. Fuentes de Conocimiento

El conocimiento del modelo proviene de una fusión entre administración de sistemas moderna y material académico clásico "Legacy".
**A. Material Académico (Legacy & Core)**

Se han integrado ejercicios y teoría de apuntes académicos para asegurar que el modelo apruebe exámenes teóricos y conozca herramientas antiguas pero vigentes en sistemas heredados:

* **Lógica de Permisos y Ficheros**: Ejercicios de creación de estructuras de directorios anidadas, uso de enlaces simbólicos y lógica de permisos octal/simbólica.
* **Herramientas Clásicas**: Gestión de RAID por software mediante raidtools (raidhotadd, raidstart) , gestión de cuotas de disco (edquota, repquota) y configuración de red clásica (ifconfig, route).
* **Multimedia y Grabación**: Uso de herramientas específicas como cdrecord y growisofs para grabación de medios ópticos , así como conversión de formatos con lame, oggenc y ffmpeg.
* **Conversión y Texto**: Herramientas de procesamiento de texto y conversión de formatos (tidy, pdftops, figlet).

**B. Administración Moderna (DevOps & Cloud)**

Se ha complementado el material académico con comandos de la industria actual:

* **Containerización**: Docker, Docker Compose, Kubernetes (kubectl).
* **Cloud**: AWS CLI, Google Cloud SDK.
* **Sistemas Modernos**: Systemd (systemctl, journalctl), gestión de paquetes moderna (dnf, apt, snap), y redes modernas (iproute2, nmcli, ss).
* **Scripting**: One-liners avanzados de Bash usando awk, sed, grep y bucles.

## 4. Ingeniería de Datos: Estrategia "Many-to-One"

Para dotar al modelo de una capacidad de comprensión humana robusta, se ha aplicado una técnica de Aumento de Datos Lingüístico (Linguistic Data Augmentation).
El objetivo es evitar el overfitting (memorización de frases exactas) y fomentar la comprensión de la intención del usuario.
**Niveles de Registro (Tone Variations)**
Cada comando técnico crítico ha sido instruido con múltiples variaciones de tono:

| Nivel | Ejemplo de Input | Output | Objetivo |
| --- | --- | --- | --- |
| Técnico | """Lista el contenido del directorio incluyendo ocultos""" | ls -la | Precisión técnica y documentación. |
| Académico | """Muestra todos los ficheros del directorio actual""" | ls -la | Resolución de ejercicios de clase. |
| Coloquial | """Enséñame todo lo que hay aquí""" | ls -la | Interacción natural día a día. |
| Jerga/Slang | """Limpia la pantalla que no veo nada""" | clear | Soporte en situaciones de estrés o confianza. |
| Urgencia | """Mata ese proceso a lo bruto""" | kill -9 PID | Gestión de incidentes críticos. |

## 5. Categorías del Dataset

El dataset cubre las siguientes áreas de competencia:

* **Gestión de Archivos**: Manipulación, búsqueda (find, grep), permisos (chmod, chown, umask) y atributos extendidos (chattr).
* **Gestión de Paquetes**: Diferenciación explícita entre Debian/Ubuntu (apt, dpkg) y Fedora/RHEL (dnf, rpm), incluyendo gestión de repositorios.
* **Redes y Seguridad**: Diagnóstico: ping, traceroute, dig, nmap.
 * **Configuración**: ip, ifconfig, nmcli.
 * **Firewall**: iptables, ufw, firewalld.
 * **Cifrado/SSH**: ssh, gpg, openssl.
 * **Sistema y Procesos**: Monitorización (top, htop, vmstat), gestión de servicios (systemd), logs (journalctl) y kernel (modprobe, sysctl).
* **Almacenamiento**: LVM, particionado (fdisk, cfdisk), sistemas de archivos (mkfs, mount), RAID y Cuotas.
* **Desarrollo**: Git, Python (pip, venv), compilación (gcc, make).

## 6. Desglose de datos por categoria 

| Categoría | Cantidad | Ejemplos Típicos |
| --- | --- | --- |
| Otros / Varios | 743 | Comandos complejos, awk avanzados, one-liners, pv, lshw, xargs, etc. |
| Sistema y Procesos | 375 | systemctl, top, kill, shutdown, history, date. |
| Archivos y Ficheros | 340 | ls, cd, cp, tar, find, du, df. |
| Redes e Internet | 337 | ping, ip, curl, ssh, nmap, iptables. |
| Filtrado y Texto | 284 | grep, sed, cat, sort, wc, tail. |
| Gestión de Paquetes | 150 | apt, dnf, pip, npm, dpkg. |
| Usuarios y Permisos | 121 | useradd, chmod, chown, passwd, sudo. |
| Docker y Contenedores | 101 | docker, docker-compose, kubectl. |
| Seguridad y Cifrado | 73 | gpg, openssl, ssh-keygen, md5sum. |
| Git / Control Versiones | 53 | git status, git commit, git push. |
| Desarrollo | 31 | python, gcc, make, java. |