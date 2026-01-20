# Entrenamiento del Modelo Conversacional: NEOPapaya Trainer

Este documento explica el proceso técnico de entrenamiento del modelo de IA de NEOPapaya (`tools/train_chat.py`), enfocado en la robustez y la eficiencia en hardware limitado.

## 1. Pipeline de Entrenamiento

El proceso de entrenamiento sigue un pipeline ETL (Extract, Transform, Load) clásico adaptado a NLP (Procesamiento de Lenguaje Natural).

1. **Ingesta (Extract)**: Carga de archivos JSON desde `training_data/`. Soporta tanto listas planas de mensajes como listas de conversaciones (listas de listas).
2. **Preprocesamiento (Transform)**:
 * Generación de pares `(Input, Target)`.
 * Aplicación de ventana deslizante para inyectar contexto (Turno anterior + Turno actual).
3. **Vectorización (Model)**: Ajuste (`fit`) del vectorizador TF-IDF sobre los inputs.
4. **Persistencia (Load)**:
 * Serialización del modelo (`pickle`) a `BrainNut/chat_model.pkl`.
 * Almacenamiento de respuestas textuales en SQLite `BrainNut/chat.db`.

## 2. Subword Matching y N-Grams

Una de las características clave de NEOPapaya Chat v2 es su capacidad para entender palabras mal escritas, jerga o variaciones sin haberlas visto explícitamente. Esto se logra mediante **N-Grams de Caracteres**.

### 2.1. El Problema de las Palabras Completas
En modelos tradicionales (Bag of Words), el vocabulario es rígido:
* Entrenamiento: "computadora"
* Input Usuario: "compu"
* **Resultado**: 0% Similitud (Son tokens totalmente distintos).

### 2.2. La Solución: Character N-Grams
Configuramos el vectorizador `TfidfVectorizer` con los siguientes hiperparámetros:
* `analyzer='char_wb'`: Analiza caracteres dentro de los límites de las palabras.
* `ngram_range=(3, 5)`: Genera tokens de 3, 4 y 5 caracteres.

#### Ejemplo Práctico
Si entrenamos con la palabra **"computadora"**, el sistema no aprende la palabra entera, sino sus fragmentos constituyentes:

* **3-grams**: `com`, `omp`, `mpu`, `put`, `uta`, `tad`, `ado`, `dor`, `ora`
* **4-grams**: `comp`, `ompu`, `mput`, ...
* **5-grams**: `compu`, `omput`, ...

Si el usuario escribe **"computadorra"** (typo) o **"compu"** (jerga):

1. **"compu"** genera: `com`, `omp`, `mpu`, `comp`, `ompu`, `compu`.
2. **Comparación**: El sistema detecta que **todos** los n-grams de "compu" están presentes en el vector de "computadora".
3. **Resultado**: La similitud matemática es muy alta, aunque las palabras no sean idénticas.

### 2.3. Beneficios Técnicos
1. **Resistencia a Typos**: "ola" vs "hola", "k ase" vs "que haces".
2. **Reducción de Dimensionalidad**: No necesitamos un diccionario infinito de todas las palabras posibles, solo de las combinaciones de caracteres comunes.
3. **Sin Lematización**: No hace falta reducir "corriendo" a "correr", ya que comparten la raíz "corr".

## 3. Ejecución del Entrenamiento

Para reentrenar el modelo tras añadir nuevos datos:

```bash
python3 tools/train_chat.py
```

Esto regenerará los artefactos en `BrainNut/` y el sistema los cargará automáticamente en el próximo reinicio.
