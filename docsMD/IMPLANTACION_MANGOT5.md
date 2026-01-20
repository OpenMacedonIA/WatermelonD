# IMPLANTACIÓN DE MANGO T5: Guía Técnica

**Versión:** 1.0
**Fecha:** 18/12/2025
**Proyecto:** NEOPapaya - Sysadmin AI

## 1. Introducción

Este documento detalla la integración del modelo **MANGO T5** (Fine-Tuned for Bash) en la arquitectura del sistema NEOPapaya. Esta actualización introduce una capacidad especializada de "Natural Language to Bash" (NL2Bash), permitiendo al asistente ejecutar comandos de sistema complejos con alta precisión sintáctica, algo que los modelos de chat generalistas (Llama/Qwen) no logran de forma fiable.

## 2. Arquitectura Implementada

### 2.1 Componentes Nuevos

* **`modules/mango_manager.py`**: Nuevo gestor encargado de cargar el modelo T5 y realizar inferencias.
 * **Modelo**: Carga artefactos desde el directorio `MANGOT5/` usando `transformers` (Hugging Face).
 * **Inferencia**: Utiliza generación secuencial (Beam Search) para traducir texto a código.
 * **Salida**: Retorna el comando generado y un *score* de confianza.

### 2.2 Integración en NeoCore (Advanced Workflow)

El flujo de procesamiento ha sido reescrito para potenciar a MANGO como motor principal:

1. **Context Injection**: Antes de invocar al modelo, se enriquece el prompt con variables de entorno (`PWD`, `User`, `Date`, `IP`).
2. **MANGO T5 (Prioridad Alta)**: Se consulta el modelo *antes* que los intents tradicionales.
 * Si confianza > 0.85: Se asume control total.
3. **Self-Correction Loop**: Si el comando generado falla al ejecutarse:
 * Se captura el error (`stderr`).
 * Se solicita a MANGO una corrección ("Fix command X taking error Y into account").
 * Se reintenta la ejecución (Max 1 reintento).
4. **Fallback**: Si MANGO falla o la confianza es baja, se recurre a `IntentManager` (Reglas Legacy) y finalmente a Chat (Llama/Gemma).

## 3. Requisitos de Ejecución

Se han añadido las siguientes dependencias al `requirements.txt`:
* `transformers`: Librería base para manejar modelos Hugging Face.
* `torch`: Framework de Deep Learning (PyTorch).
* `sentencepiece`: Tokenizer necesario para modelos T5.

## 4. Instrucciones de Uso

### 4.1 Comandos Automáticos
El usuario puede pedir información de lectura segura:
> *"Busca los archivos en /home"* -> Ejecuta `ls` o `find` inmediatamente.

### 4.2 Comandos Críticos
Para acciones de modificación:
> *"Reinicia el servicio nginx"* -> MANGO genera `systemctl restart nginx`.
> **NEOPapaya**: *"He generado el comando: systemctl restart nginx. ¿Quieres que lo ejecute?"*
> **Usuario**: *"Sí"* -> Se ejecuta.

## 5. Mantenimiento y Optimización

* **Modelo**: Si se entrena una nueva versión de MANGO, basta con reemplazar los archivos en la carpeta `MANGOT5`.
* **Safety**: La lista de comandos seguros ("whitelist") está hardcodeada en `NeoCore.py` y debería expandirse según se validen más casos de uso.
* **Hardware**: Actualmente corre en CPU (por defecto en i3/8GB). Si se dispone de GPU, `MangoManager` intentará usar CUDA automáticamente.
