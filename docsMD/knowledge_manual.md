# Manual de Gestión de Conocimiento (Knowledge Base)

## Introducción
El módulo de **Conocimiento** permite a NEOPapaya almacenar y recuperar información clave-valor de manera persistente. Esto es útil para que el asistente "recuerde" datos específicos, preferencias de usuario o configuraciones personalizadas que no están cubiertas por los intents estándar.

## Acceso
Para acceder al gestor de conocimiento:
1. Inicia sesión en el panel web (`http://<IP>:5000`).
2. Navega a la sección **Conocimiento** en el menú lateral.

## Añadir un Nuevo Dato
1. Haz clic en el botón azul **+ Añadir Dato** en la parte superior derecha.
2. Se abrirá un formulario con dos campos:
 - **Clave (Key)**: El identificador único del dato. Por ejemplo: `cumpleaños_jorge`, `wifi_invitados`, `codigo_alarma`.
 - *Nota*: Usa nombres descriptivos y sin espacios (usa guiones bajos `_`) para facilitar su uso futuro en scripts o skills.
 - **Valor (Value)**: La información que quieres guardar. Puede ser texto, números o incluso pequeños fragmentos de JSON.
3. Haz clic en **Guardar**.

## Editar y Borrar
- **Editar**: Haz clic en el icono de lápiz junto a un dato existente para modificar su valor.
- **Borrar**: Haz clic en el icono de papelera para eliminar el dato permanentemente.

## Uso en Skills (Desarrolladores)
Las skills pueden acceder a estos datos a través del `DatabaseManager` o `MemoryManager`.

```python
# Ejemplo conceptual
cumple = self.core.memory.get("cumpleaños_jorge")
self.speak(f"El cumpleaños de Jorge es el {cumple}")
```

## Casos de Uso Comunes
- **Recordatorios estáticos**: "clave_wifi", "direccion_oficina".
- **Preferencias**: "color_favorito", "temperatura_ideal".
- **Tokens**: "api_key_weather" (aunque se recomienda usar variables de entorno para datos sensibles).
