# 🥭 MANGO: The No-Nonsense Sysadmin AI

> **"Less Chat, More Bash."**

**MANGO** es un Modelo de Lenguaje Pequeño (SLM) de 1.5 Billones de parámetros, diseñado con un único propósito: **Traducir lenguaje natural a comandos de terminal Linux precisos y peligrosamente efectivos.**

![Banner](https://img.shields.io/badge/Model-Salesforce--CodeT5-blue) ![License](https://img.shields.io/badge/License-Apache_2.0-green) ![Training](https://img.shields.io/badge/Training-Google_Colab_T4-orange) ![Framework](https://img.shields.io/badge/Framework-Unsloth-yellow)

## 📖 Descripción

A diferencia de ChatGPT o modelos generalistas, Mango no quiere ser tu amigo. No saluda, no da explicaciones innecesarias y no te dice "Aquí tienes una lista de opciones".
Mango ha sido entrenado ("lobotomizado") para eliminar la verborrea conversacional y actuar como un motor de traducción estricto.

* **Input:** "Búscame los archivos .log modificados hoy y bórralos"
* **Output:** `find / -name "*.log" -mtime -1 -delete`

Basado en **salesforce/codet5-base** y acelerado con **Unsloth**, Mango hereda una comprensión profunda de la lógica de programación, pero refinada mediante Fine-Tuning para especializarse en la administración de sistemas Linux.

## 🚀 Inicio Rápido (Ollama)

La forma más fácil de usar Mango es descargando el GGUF y usándolo en [Ollama](https://ollama.com/).

### 1. Modelfile
Mango necesita reglas estrictas para no "alucinar". Crea un archivo llamado `Modelfile`:

```dockerfile
FROM ./mango-v1-q4_k_m.gguf

# Temperatura 0 para determinismo absoluto (crucial para sysadmin)
PARAMETER temperature 0.0
PARAMETER num_ctx 4096

SYSTEM """
Eres Mango, un asistente CLI experto.
Tu única función es traducir lenguaje natural a comandos Bash de Linux.
NO des explicaciones. NO saludes.
Responde ÚNICAMENTE con el bloque de código.
"""

# Template anti-echoing
TEMPLATE """User: {{ .Prompt }}
Assistant: ```bash
"""

PARAMETER stop "User:"
PARAMETER stop "Assistant:"
PARAMETER stop "```"
``` 

### 2. Ejecución
```bash
ollama create mango -f Modelfile
ollama run mango
```

### Ejemplo:
```plaintext
>>> comprime la carpeta /var/log en un tar.gz excluyendo los errores
tar -czvf logs_backup.tar.gz /var/log --exclude='*error*'
```

## ⚙️ Detalles del Entrenamiento

Mango fue entrenado utilizando recursos accesibles para demostrar la democratización de la IA.

* **Modelo Base**: salesforce/codet5-base
* **Método**: QLoRA (4-bit quantization)
* **Infraestructura**: Google Colab Free Tier (NVIDIA Tesla T4 16GB).
* **Framework**: Unsloth (Optimización de velocidad 2x y reducción de memoria).
* **Limpieza de Datos**: Dataset híbrido (Privado + NL2Bash + Commandlinefu) limpiado con Regex para forzar estructura Markdown.

## ⚠️ Advertencia y Responsabilidad

Mango genera comandos ejecutables. Aunque el modelo intenta ser preciso, SIEMPRE revisa el comando antes de presionar Enter. Los autores no se hacen responsables de pérdidas de datos, servidores rotos o ```rm -rf /``` accidentales.

## 🤝 Créditos

Creado como un experimento de IA eficiente.

* **Base Model**: Salesforce Research
* **Accelerated by**: Unsloth AI