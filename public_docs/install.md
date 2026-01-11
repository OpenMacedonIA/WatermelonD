# Guía de Instalación de Neo

Este documento detalla los diferentes métodos de instalación disponibles para el sistema Neo. El sistema ha sido diseñado para ser modular, permitiendo separar el núcleo de procesamiento de la interfaz de usuario.
> Este documento se encuentra desactualizado

## Requisitos Previos

- Sistema Operativo: Linux (Debian 12, Ubuntu 22.04+, Fedora 38+ recomendado).
- Git instalado.
- Distrobox y Podman/Docker (el script de instalación intentará instalarlos si no existen).

## Métodos de Instalación

Para simplificar el despliegue, se proporciona un asistente unificado (`install_wizard.sh`) que le guiará a través del proceso.

Para iniciar, ejecute:

```bash
./install_wizard.sh
```

El asistente le ofrecerá tres opciones principales:

### 1. Nodo Principal (Instalación Completa)

**Descripción:**  
Instala tanto el núcleo del sistema (NeoCore) como la interfaz web en el mismo equipo.

**Caso de uso:**  
Ideal para ordenadores de escritorio, portátiles o Raspberry Pi 5 donde se desea tener todo el sistema autocontenido. El usuario interactúa con la interfaz web en `http://localhost:5000` desde el mismo equipo.

**Pasos:**
1. Seleccione la opción 1 en el asistente.
2. El sistema creará un contenedor Distrobox (`neocore-box`).
3. Se instalarán todas las dependencias de IA, Voz y Web.
4. Al finalizar, use `./run_neocore_distrobox.sh` para iniciar.

### 2. Nodo Principal Headless (Solo Núcleo)

**Descripción:**  
Instala únicamente el núcleo de procesamiento (NeoCore) y la API, sin lanzar la interfaz gráfica localmente.

**Caso de uso:**  
Recomendado para servidores, Raspberry Pi Zero/3/4 o mini-PCs que actuarán como "cerebro" central. Este nodo procesará la voz, las automatizaciones y servirá la API, pero se espera que se controle desde otro dispositivo.

**Pasos:**
1. Seleccione la opción 2 en el asistente.
2. El proceso es similar al completo, pero se optimiza para no requerir recursos gráficos.
3. Durante la instalación, se le pedirá seleccionar la versión del modelo **MANGO**:
   - **MANGO2 (Recomendado)**: Versión avanzada con mayores conocimientos.
   - **MANGO (Estable)**: Versión anterior más probada.
4. El sistema estará disponible en la red local en el puerto 5000 (API).

### 3. Cliente Web Remoto (Solo Interfaz)

**Descripción:**  
Instala una aplicación web ligera que actúa como "mando a distancia" para un Nodo Principal existente.

**Caso de uso:**  
Ideal si tiene NeoCore corriendo en una Raspberry Pi en el salón y quiere controlarlo cómodamente desde su PC de trabajo, tablet o portátil sin necesidad de instalar toda la inteligencia artificial en cada dispositivo.

**Pasos:**
1. Asegúrese de tener un Nodo Principal (Opción 1 o 2) ya funcionando en su red.
2. Anote la dirección IP y puerto del Nodo Principal (ejemplo: `http://192.168.1.50:5000`).
3. En el equipo cliente, ejecute `./install_wizard.sh` y seleccione la opción 3.
4. Introduzca la IP del Nodo Principal cuando se le solicite.
5. Se generará un script `run_client.sh`.
6. Ejecute `./run_client.sh` para abrir la interfaz de control.

## Estructura de Scripts

Si prefiere la instalación manual o necesita depurar, estos son los scripts subyacentes:

- `install_wizard.sh`: Menú principal. Es el punto de entrada recomendado.
- `setup_distrobox.sh`: Script de bajo nivel que crea el contenedor Debian y configura el entorno virtual `venv`. Usado por las opciones 1 y 2.
- `run_neocore_distrobox.sh`: Lanzador del Nodo Principal. Entra en el contenedor y ejecuta el sistema.
- `web_client/app.py`: El código de la interfaz remota (usado por la opción 3).

## Solución de Problemas Comunes

**Error: "Connection refused" en el Cliente Remoto**  
Asegúrese de que el Nodo Principal está encendido y que el firewall permite conexiones al puerto 5000 (o el configurado).

**Error: Dependencias faltantes**  
Si falla el arranque, intente ejecutar `./setup_distrobox.sh` nuevamente para reparar el entorno.
