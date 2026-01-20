# ️ Web Interface Roadmap (Future Ideas)

Este documento recoge ideas y planes futuros para evolucionar la interfaz web de WatermelonD, centrándose en la experiencia de usuario (UX), personalización y nuevas funcionalidades.

## Completado en v2.6.0 (Cosmic Update)

- **Rediseño Visual Completo**: Tema "Cosmic" con modo claro/oscuro.
- **Personalización CSS**: Editor de CSS en ajustes.
- **Responsividad**: Mejoras críticas para uso en móviles y tablets.
- **Update OTA**: Actualización desde la web sin sudo.
- **Explorador de Archivos**: Búsqueda/Filtrado en tiempo real.

## Experiencia de Usuario y Diseño

- [X] **Tablero Personalizable (Drag & Drop)**:

- Permitir mover, redimensionar y ocultar widgets del Dashboard.
- Guardar la disposición por usuario.

- [ ] **Editor de Temas Visual**:

- Herramienta GUI para cambiar los colores de acento, fuentes y bordes sin tocar CSS.
- Soporte para temas comunitarios (importar/exportar JSON).

- [ ] **Modo "Focus" / "Zen"**:

- Una vista minimalista que solo muestre la hora, el clima y el estado de la música/tarea actual. Ideal para pantallas "Always On".

## Movilidad y PWA

- [ ] **Soporte PWA (Progressive Web App)**:

- Hacer que la web sea instalable en Android/iOS como una app nativa.
- Soporte offline básico (caché de interfaz).

- [ ] **Notificaciones Push Nativas**:

- Enviar alertas (alarma, timbre, error crítico) al móvil aunque la web esté cerrada.

- [X] **Control por Voz en el Navegador**:

- Usar la Web Speech API para hablar con WatermelonD directamente desde el móvil/PC sin necesidad de micrófono en el servidor central.

## ️ Herramientas Avanzadas

- [ ] **Explorador de Archivos 2.0**:

- Vista de galería para imágenes.
- Editor de texto con resaltado de sintaxis (Monaco Editor) integrado.
- Subida de archivos arrastrando (Drag & Drop).

- [X] **Terminal Web Mejorada**:

- Soporte para pestañas múltiples.
- Historial de comandos persistente.
- Autocompletado visual.

- [ ] **Gestor de Dockers Visual**:

- Crear contenedores desde un formulario (sin CLI).
- Ver logs en tiempo real con colores.
- Tienda de aplicaciones "One-Click" (plantillas de docker-compose predefinidas).

## Visualización de Datos

- [ ] **Gráficos Interactivos**:

- Histórico de temperatura/uso de CPU (últimas 24h, semana, mes).
- Gráficos de red estilo "Speedtest".

- [ ] **Mapa de Red**:

- Visualización visual de dispositivos conectados a la WiFi (topología).

## Seguridad

- [ ] **Autenticación Multi-Usuario**:

- Roles (Admin, Usuario, Invitado).
- Permisos granulares (ej: Invitado solo puede controlar música, no terminal).

- [ ] **2FA (Doble Factor)**:

- Opcional para acceso remoto fuera de casa.
