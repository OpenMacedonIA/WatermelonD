# Manual de Despliegue Avanzado: Debian Minimal (Desde 0)

Este documento detalla el proceso para realizar una instalación mínima y optimizada de Debian, orientada a servidores o sistemas embebidos donde se requiere el máximo rendimiento y control.

## 1. Requisitos Previos

*   **ISO**: Descargar `debian-netinst` (Network Installer) desde [debian.org](https://www.debian.org/distrib/netinst). Es la imagen más pequeña y descarga solo lo necesario durante la instalación.
*   **Medio de instalación**: USB booteable (creado con `dd`, Etcher o Rufus).
*   **Conexión a Internet**: Indispensable (por cable ethernet preferiblemente) para descargar paquetes durante la instalación.

## 2. Instalación del Sistema Base (Paso a Paso)

1.  **Boot**: Inicia desde el USB.
2.  **Installer Menu**: Selecciona "Install" (o "Graphical Install" si prefieres ratón, pero el modo texto es más rápido y "auténtico").
3.  **Language/Location**: Selecciona idioma (recomendado English para servidores, o Español si prefieres), ubicación y teclado.
4.  **Hostname**: Asigna un nombre (ej. `WatermelonD-server`).
5.  **Domain**: Déjalo vacío si no tienes dominio.
6.  **Root Password**: **IMPORTANTE**: Si dejas esto en blanco, el instalador configurará `sudo` automáticamente para el primer usuario que crees. *Recomendación: Déjalo en blanco para un setup más moderno tipo Ubuntu.*
7.  **User Account**: Crea tu usuario principal (ej. `admin` o tu nombre).
8.  **Partitioning**:
    *   *Método*: "Guided - use entire disk" es lo más fácil.
    *   *Avanzado*: Si sabes lo que haces, crea particiones separadas para `/var` y `/home` para evitar llenar la raíz con logs.
    *   *Swap*: Recomendado al menos 1GB o igual a la RAM si es poca.
9.  **Base System**: Se instalará el núcleo.
10. **Package Manager**: Elige un espejo (mirror) cercano a tu ubicación (ej. `ftp.es.debian.org`).
    *   *Proxy*: Déjalo vacío si no usas.
11. **Software Selection (CRÍTICO)**:
    *   Aquí es donde se define la instalación "mínima".
    *   **DESMARCA TODO** excepto:
        *   `[*] SSH server` (Fundamental para acceso remoto).
        *   `[*] Standard system utilities` (Herramientas básicas).
    *   **NO MARQUES**: "Debian desktop environment" ni "GNOME", "Xfce", etc. Queremos un sistema sin entorno gráfico preinstalado.
12. **GRUB**: Instala el cargador de arranque en el disco principal (`/dev/sda` o `/dev/nvme...`).
13. **Finalizar**: Reinicia y retira el USB.

## 3. Post-Instalación y Configuración Inicial

Accede vía SSH o consola local.

### 3.1. Sudo (si pusiste pass de root)
Si definiste contraseña de root, tu usuario no tendrá sudo.
```bash
su -
apt install sudo
usermod -aG sudo tu_usuario
exit
# Logueate de nuevo
```

### 3.2. Red (Network Manager)
En instalaciones mínimas a veces solo tienes `ip` o editar `/etc/network/interfaces`. Para facilitar la vida:
```bash
sudo apt install network-manager
sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager
# Usar nmtui para configurar wifi/ip visualmente
sudo apt install network-manager-gnome # (Opcional, trae nm-applet pero nmtui es CLI)
```

### 3.3. Optimización de Swappiness (Opcional)
Para evitar usar swap demasiado pronto:
```bash
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 4. Software Esencial Recomendado

Para tener un entorno de terminal robusto y listo para desplegar aplicaciones (como WatermelonD/WatermelonD), instala este pack básico:

```bash
sudo apt update && sudo apt install -y \
    curl wget git \
    vim nano \
    htop tree \
    net-tools \
    ufw \
    unzip \
    build-essential
```

*   **Editores**: `vim` y `nano` (para gustos colores).
*   **Monitorización**: `htop` (mejor que top).
*   **Red**: `net-tools` (ifconfig, netstat), `ufw` (firewall simple).
*   **Utilidades**: `git` (control versiones), `curl`/`wget` (descargas), `unzip`.

## 5. Seguridad Básica (UFW)

Configura el firewall para permitir solo SSH y lo que necesites:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
# Si vas a usar servidor web:
# sudo ufw allow 80/tcp
# sudo ufw allow 443/tcp
sudo ufw enable
```

## 6. Siguientes Pasos (Despliegue del Proyecto)

Una vez tengas el sistema base listo:

1.  Clona tu repositorio:
    ```bash
    git clone https://github.com/tu_usuario/WatermelonD.git
    cd WatermelonD
    ```
2.  Ejecuta el script de instalación del proyecto (que se encargará de dependencias específicas, Python, Docker, etc.):
    ```bash
    ./install.sh
    ```

---
*Este manual garantiza un sistema limpio, rápido y sin "bloatware", ideal para producción.*
