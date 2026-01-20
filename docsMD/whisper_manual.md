# Manual de Optimización de Whisper (Hybrid STT)

Este documento explica cómo configurar el sistema de reconocimiento de voz **Híbrido** (Vosk + Whisper) para WatermelonD Nano.

## Arquitectura Híbrida

En sistemas x86_64 (como tu i3 con Fedora), utilizamos lo mejor de dos mundos:
1. **Vosk**: Escucha continuamente la palabra clave ("WatermelonD", "Tío"). Es instantáneo y consume muy poca CPU.
2. **Whisper**: Se activa SOLO cuando se detecta la palabra clave. Transcribe el comando completo con máxima precisión.

## 1. Requisitos Previos

```bash
pip install faster-whisper
sudo dnf install ffmpeg# En Fedora
```

## 2. Uso de la Herramienta de Optimización

El script `tools/optimize_whisper.py` ahora soporta configuración automática.

### Para Intel i3 (7ª Gen) + 8GB RAM

Recomendamos el modelo `base` o `small` cuantizado a `int8`.

```bash
# Prueba el modelo 'base' y si funciona bien, actualiza la configuración automáticamente
python3 tools/optimize_whisper.py --model base --quantization int8 --auto-configure
```

Si el RTF es menor a 0.5 (muy rápido), puedes probar con `small` para mayor precisión:

```bash
python3 tools/optimize_whisper.py --model small --quantization int8 --auto-configure
```

### ¿Qué es el RTF?
- **RTF < 1.0**: Apto para tiempo real.
- **RTF > 1.0**: Demasiado lento.

## 3. Configuración Manual (config.json)

Si prefieres editar `config.json` a mano:

```json
"stt": {
 "engine": "hybrid",
 "whisper_model": "base",
 "whisper_device": "cpu",
 "whisper_compute": "int8",
 "input_device_index": null
}
```

## 4. Solución de Problemas

- **Error "Illegal instruction"**: Tu CPU no soporta las instrucciones vectoriales necesarias. RPi 3 y anteriores pueden tener problemas.
- **Memoria insuficiente**: Si el script se cierra solo (Killed), es que te has quedado sin RAM. Usa un modelo más pequeño (`tiny`) o aumenta la swap.
