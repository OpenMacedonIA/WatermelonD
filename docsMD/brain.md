# Arquitectura Cognitiva: WatermelonD BrainNut

Este documento detalla el funcionamiento interno del sistema de memoria y "razonamiento" de WatermelonD, implementado en los módulos `BrainNut.py` y `chat.py`.

## 1. Memoria Estructurada (`modules/BrainNut.py`)

El componente `BrainNut` actúa como el hipocampo del sistema, gestionando la persistencia de datos explícitos y la memoria de trabajo a corto plazo.

### 1.1. Persistencia (SQLite)
Se utiliza **SQLite** (`BrainNut.db`) por su naturaleza ACID, ligereza y cero configuración. El esquema relacional consta de tres tablas principales:

* **`interactions`**: Registro histórico (Log).
 * Campos: `id`, `timestamp`, `user_input`, `neo_response`, `intent`.
 * Uso: Auditoría y potencial reentrenamiento futuro.
* **`facts`**: Memoria semántica (Datos).
 * Campos: `key` (PK), `value`.
 * Uso: Almacenar información arbitraria enseñada por el usuario ("La IP del servidor es 192.168.1.50").
* **`aliases`**: Memoria asociativa.
 * Campos: `trigger` (PK), `command`.
 * Uso: Mapeo directo de frases personalizadas a comandos internos.

### 1.2. Memoria de Trabajo (Short-Term Memory)
Implementada mediante una estructura de datos `collections.deque` con `maxlen=5`.
* **Propósito**: Mantener el contexto inmediato de la conversación.
* **Funcionamiento**: Almacena los últimos 5 objetos de interacción. Cuando entra uno nuevo, el más antiguo se descarta automáticamente (FIFO).

---

## 2. Motor Conversacional (`modules/chat.py`)

Cuando WatermelonD no reconoce un comando explícito (Intent Matching fallido), activa el subsistema de **Recuperación de Respuesta Generativa (Retrieval-Based Chatbot)**.

### 2.1. Modelo Vectorial (TF-IDF)
El núcleo del sistema es un modelo de **Frecuencia de Término - Frecuencia Inversa de Documento (TF-IDF)**.

* **Matematización del Lenguaje**: Convertimos las frases de texto en vectores numéricos de alta dimensión.
* **Similitud del Coseno**: Para encontrar la mejor respuesta, calculamos el coseno del ángulo entre el vector de entrada del usuario y los vectores de todas las frases conocidas en la base de datos de entrenamiento.
 * `Similitud = 1.0`: Coincidencia exacta.
 * `Similitud ~ 0.0`: Ortogonalidad (sin relación).

### 2.2. Gestión de Contexto (Sliding Window)
Para simular una comprensión del hilo conversacional, no analizamos las frases de forma aislada.

* **Input Contextual**: El vector de entrada no es solo `Input_Usuario`, sino una concatenación:
 $$Vector_{input} = Vector(Respuesta_{Neo_{-1}} + " ||| " + Input_{Usuario})$$
* **Efecto**: Esto permite desambiguar frases cortas. Un "Sí" después de "¿Quieres música?" tiene un vector muy diferente a un "Sí" después de "¿Apago el sistema?".

### 2.3. Robustez (N-Grams)
El sistema utiliza **N-Grams de caracteres** (ver `train.md`) para tolerar fallos ortográficos y variaciones morfológicas sin necesidad de lematización compleja.
