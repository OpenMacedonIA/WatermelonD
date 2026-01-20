# MANGO: Documentación Técnica del Asistente Sysadmin AI
**Versión:** 1.0.0 
**Fecha:** 16 de Diciembre de 2024 
**Proyecto:** Mango (Sysadmin LLM) 
**Arquitectura:** Fine-Tuning sobre salesforce/codet5-base 
**Infraestructura:** Google Colab (Tesla T4)

---

## Índice de Contenidos

1. [Introducción y Objetivos](#1-introducción-y-objetivos)
2. [Arquitectura del Modelo](#2-arquitectura-del-modelo)
 2.1. Selección del Modelo Base (Salesforce/CodeT5)
 2.2. Justificación del Cambio a Code-LLM
3. [Ingeniería de Datos (Dataset)](#3-ingeniería-de-datos-dataset)
 3.1. Fuentes de Datos y Limpieza Regex
 3.2. Estructura del Prompt (Template)
4. [Metodología de Entrenamiento (Fine-Tuning)](#4-metodología-de-entrenamiento-fine-tuning)
 4.1. Entorno de Ejecución (Google Colab T4)
 4.2. Aceleración con Unsloth
 4.3. Hiperparámetros
5. [Despliegue e Inferencia](#5-despliegue-e-inferencia)
 5.1. Conversión a GGUF
 5.2. Configuración de Ollama (Modelfile)
6. [Anexos: Código Fuente](#6-anexos-código-fuente)

---

## 1. Introducción y Objetivos

El proyecto **MANGO** tiene como objetivo desarrollar un Modelo de Lenguaje Pequeño (SLM) especializado en administración de sistemas Linux. El modelo está diseñado para ser entrenado de manera accesible utilizando recursos gratuitos en la nube (Google Colab Free Tier) y desplegado localmente en cualquier hardware modesto.

### 1.1. El Problema
Los modelos generalistas sufren de "verborrea conversacional" (chatty behavior) y alucinaciones técnicas. Un Sysadmin necesita un motor de traducción **Lenguaje Natural -> Bash** estricto, sin saludos ni explicaciones superfluas.

---

## 2. Arquitectura del Modelo

### 2.1. Selección del Modelo: Salesforce CodeT5
Se seleccionó `salesforce/codet5-base` frente a `Qwen/TinyLlama` por su arquitectura encoder-decoder, ideal para traducción de lenguaje natural a código.
* **Pre-entrenamiento:** Incluye datasets masivos de código (GitHub), permitiendo entender tuberías (pipes), awk, sed y regex nativamente.
* **Eficiencia:** Con 1.5B parámetros, es el tamaño límite perfecto para ser entrenado en la VRAM limitada (15GB) de una Tesla T4 y ejecutado posteriormente en portátiles.

---

## 3. Ingeniería de Datos (Dataset)

La estrategia de datos se centró en la limpieza agresiva para eliminar el formato "chat" y forzar un formato "instrucción".

### 3.1. Fuentes y Limpieza
Se combinaron datasets públicos (NL2Bash, Commandlinefu) con un archivo privado `gold_commands.jsonl`.
Se desarrolló un script de pre-procesamiento con **Expresiones Regulares (Regex)** para sanear líneas corruptas (e.g., ``) que rompían el pipeline de entrenamiento estándar.

### 3.2. Template de Entrenamiento
Se estandarizó el input para condicionar al modelo a responder siempre con bloques de código Markdown:

```text
User: {instrucción}
Assistant: ```bash
{comando}
```
---

## 4. Metodología de Entrenamiento

### 4.1. Entorno: Google Colab (Tesla T4)
El entrenamiento se realizó en una instancia estándar de Google Colab equipada con una GPU NVIDIA Tesla T4 (16GB VRAM).

### 4.2. Aceleración con Unsloth
Se utilizó la librería **Unsloth**, que optimiza la retropropagación y reduce el consumo de memoria en un 60% comparado con HuggingFace nativo. Esto permitió:
* Usar un `batch_size` mayor.
* Acelerar el entrenamiento en un 2x.
* Exportar directamente a GGUF sin pasos intermedios complejos.

### 4.3. Hiperparámetros Críticos
* **Cuantización:** 4-bit (Load in 4bit).
* **LoRA Rank (r):** 16.
* **Target Modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` (Todos los módulos lineales para máxima adaptación).
* **Epochs:** 1 (Para preservar la generalización del modelo base).
* **Learning Rate:** 2e-4.

---

## 5. Despliegue e Inferencia

### 5.1. Exportación GGUF
Gracias a Unsloth, el modelo se exportó directamente a formato GGUF (`q4_k_m`) desde el notebook de Colab, listo para su consumo en local.

### 5.2. Modelfile (Jaula de Comportamiento)
Para producción en **Ollama**, se diseñó un `Modelfile` que elimina la temperatura (creatividad = 0) y pre-escribe el inicio de la respuesta con ` ```bash ` para forzar al modelo a completar el código.

---

## 6. Anexos: Código Fuente

### Anexo A: Script de Entrenamiento (Unsloth + Colab)

```python
from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_from_disk

# 1. Configuración del Modelo
max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
 model_name = "salesforce/codet5-base",
 max_seq_length = max_seq_length,
 dtype = None,
 load_in_4bit = True,
)

# 2. Configuración LoRA
model = FastLanguageModel.get_peft_model(
 model,
 r = 16,
 target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
 "gate_proj", "up_proj", "down_proj",],
 lora_alpha = 16,
 lora_dropout = 0,
 bias = "none",
 use_gradient_checkpointing = "unsloth", 
 random_state = 3407,
)

# 3. Carga del Dataset Limpio
dataset = load_from_disk("/content/drive/MyDrive/data/output_dataset/2023-12-16_v1")

# Función de formato con EOS Token
EOS_TOKEN = tokenizer.eos_token
def formatting_prompts_func(examples):
 return {"text": [text + EOS_TOKEN for text in examples["text"]]}
dataset = dataset.map(formatting_prompts_func, batched = True)

# 4. Entrenador
trainer = SFTTrainer(
 model = model,
 tokenizer = tokenizer,
 train_dataset = dataset,
 dataset_text_field = "text",
 max_seq_length = max_seq_length,
 packing = True,
 args = TrainingArguments(
 per_device_train_batch_size = 2,
 gradient_accumulation_steps = 4,
 warmup_steps = 5,
 num_train_epochs = 1,
 learning_rate = 2e-4,
 fp16 = not torch.cuda.is_bf16_supported(),
 bf16 = torch.cuda.is_bf16_supported(),
 logging_steps = 10,
 optim = "adamw_8bit",
 output_dir = "outputs",
 ),
)

trainer.train()
