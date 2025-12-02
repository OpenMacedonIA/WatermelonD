import sqlite3
import os
import sys

# Add root directory to sys.path
sys.path.append(os.getcwd())

from modules.database import DatabaseManager

db = DatabaseManager()

# Knowledge Graph Seed Data
# (Source, Target, Relation)
relations = [
    # --- Persona TIO ---
    ("tio", "asistente ai", "es_un"),
    ("tio", "openkompai nano", "parte_de"),
    ("tio", "sarcástico", "tiene_rasgo"),
    ("tio", "útil", "tiene_rasgo"),
    ("tio", "python", "escrito_en"),
    ("creador", "jrodriiguezg", "es"), 
    
    # --- Linux / SysAdmin ---
    ("ls", "listar contenido directorio", "descripcion"),
    ("cd", "cambiar directorio", "descripcion"),
    ("grep", "buscar texto en archivos", "descripcion"),
    ("find", "buscar archivos", "descripcion"),
    ("top", "mostrar procesos linux", "descripcion"),
    ("htop", "visor de procesos interactivo", "descripcion"),
    ("df", "reportar uso espacio disco", "descripcion"),
    ("du", "estimar uso espacio archivo", "descripcion"),
    ("free", "mostrar uso memoria", "descripcion"),
    ("systemctl", "controlar sistema y servicios systemd", "descripcion"),
    ("journalctl", "consultar logs systemd", "descripcion"),
    ("chmod", "cambiar permisos archivo", "descripcion"),
    ("chown", "cambiar propietario archivo", "descripcion"),
    ("ssh", "login remoto seguro", "descripcion"),
    ("scp", "copia segura", "descripcion"),
    ("rsync", "sincronización remota archivos", "descripcion"),
    ("tar", "archivador", "descripcion"),
    ("apt", "gestor paquetes debian/ubuntu", "descripcion"),
    ("dnf", "gestor paquetes fedora", "descripcion"),
    ("ip", "mostrar / manipular rutas, dispositivos", "descripcion"),
    ("ping", "enviar eco icmp a hosts", "descripcion"),
    ("netstat", "imprimir conexiones red", "descripcion"),
    ("ss", "volcar estadísticas sockets", "descripcion"),
    ("curl", "transferir una url", "descripcion"),
    ("wget", "descargador de red no interactivo", "descripcion"),
    ("nano", "editor de texto simple", "descripcion"),
    ("vim", "vi mejorado, editor programadores", "descripcion"),
    ("cat", "concatenar archivos e imprimir", "descripcion"),
    ("tail", "mostrar parte final archivos", "descripcion"),
    ("head", "mostrar parte inicial archivos", "descripcion"),
    ("less", "opuesto de more", "descripcion"),
    ("man", "interfaz manuales sistema", "descripcion"),
    ("sudo", "ejecutar comando como otro usuario", "descripcion"),
    ("reboot", "reiniciar sistema", "descripcion"),
    ("shutdown", "apagar sistema", "descripcion"),
    
    # --- Solución de Problemas ---
    ("internet lento", "router", "revisar"),
    ("internet lento", "isp", "revisar"),
    ("internet lento", "señal wifi", "revisar"),
    ("servidor caido", "logs", "revisar"),
    ("servidor caido", "electricidad", "revisar"),
    ("servidor caido", "cable red", "revisar"),
    ("cpu alta", "top", "ejecutar"),
    ("cpu alta", "htop", "ejecutar"),
    ("memoria alta", "free -m", "ejecutar"),
    ("disco lleno", "df -h", "ejecutar"),
    ("disco lleno", "ncdu", "ejecutar"),
    ("fallo ssh", "service ssh status", "revisar"),
    ("fallo ssh", "firewall", "revisar"),
    
    # --- Componentes ---
    ("nginx", "servidor web", "es_un"),
    ("apache", "servidor web", "es_un"),
    ("mysql", "base de datos", "es_un"),
    ("postgresql", "base de datos", "es_un"),
    ("sqlite", "base de datos", "es_un"),
    ("docker", "contenedores", "es_un"),
    ("kubernetes", "orquestación", "es_un"),
    ("flask", "framework web", "es_un"),
    ("django", "framework web", "es_un"),
    ("react", "librería frontend", "es_un"),
    ("vue", "framework frontend", "es_un")
]

# Hechos (Clave-Valor)
facts = {
    "linux": "Un núcleo de sistema operativo tipo Unix de código abierto.",
    "python": "Un lenguaje de programación interpretado de alto nivel.",
    "tio": "TIO es un asistente de IA avanzado que corre en Linux.",
    "openkompai": "Un proyecto de código abierto para asistentes de IA locales.",
    "gemma": "Una familia de modelos abiertos ligeros y de última generación de Google.",
    "sqlite": "Una biblioteca en C que implementa un motor de base de datos SQL pequeño, rápido y autónomo.",
    "ssh": "Secure Shell es un protocolo de red criptográfico para operar servicios de red de forma segura.",
    "docker": "Un conjunto de productos PaaS que usan virtualización a nivel de SO para entregar software en contenedores."
}

print("Seeding Knowledge Graph & Facts...")
count_rel = 0
for source, target, rel in relations:
    if db.add_relation(source, target, rel):
        count_rel += 1

count_facts = 0
for key, value in facts.items():
    if db.add_fact(key, value):
        count_facts += 1

print(f"Seeded {count_rel} relations and {count_facts} facts.")
