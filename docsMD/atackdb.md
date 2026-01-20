# Base de Datos de Firmas de Ataque (WatermelonD Guard)

WatermelonD Guard utiliza un sistema de detección basado en firmas y anomalías. Este documento explica cómo funciona la base de datos `data/attack_signatures.json` y cómo añadir nuevas reglas.

## Estructura de una Firma

Cada entrada en el archivo JSON representa una regla de detección.

```json
{
 "id": "ID_UNICO_DEL_ATAQUE",
 "name": "Nombre legible para humanos",
 "description": "Explicación técnica",
 "source": "FUENTE_DE_DATOS",
 "pattern": "PATRON_TEXTO",
 "metric": "METRICA_NUMERICA",
 "threshold": 5,
 "window_seconds": 60,
 "severity": "high"
}
```

### Campos

* **`id`**: Identificador único (ej. `SSH_BRUTE_FORCE`).
* **`source`**: De dónde vienen los datos.
 * `log_auth`: Lee `/var/log/auth.log`.
 * `system_stats`: Métricas de CPU/RAM.
 * `net_stats`: Métricas de red.
* **`pattern`** (Solo para logs): Texto a buscar en cada línea (ej. "Failed password").
* **`metric`** (Solo para stats): Nombre de la métrica (`cpu_percent`, `syn_sent_count`).
* **`threshold`**: Cuántas veces debe ocurrir el evento (o qué valor superar) para activar la alerta.
* **`window_seconds`**: Ventana de tiempo para contar eventos (ej. 5 intentos en 60 segundos).

## Lógica de Detección (Diagrama de Flujo)

El motor `modules/guard.py` sigue este proceso:

1. **Ingesta**: Lee logs y métricas cada segundo.
2. **Filtrado**:
 * Si es LOG: ¿Contiene la línea el `pattern`?
 * Si es STAT: ¿Es el valor >= `threshold`?
3. **Acumulación**:
 * Si pasa el filtro, se guarda una marca de tiempo en memoria.
 * Se eliminan marcas más antiguas que `window_seconds`.
4. **Decisión**:
 * ¿Cantidad de marcas en ventana >= `threshold`?
 * **SÍ**: ¡ALERTA! (WatermelonD habla y loguea).
 * **NO**: Esperar.

## Ejemplos de Reglas

### Detectar Minería de Criptomonedas (CPU Alta)
```json
{
 "id": "CRYPTO_MINER",
 "source": "system_stats",
 "metric": "cpu_percent",
 "threshold": 98,
 "severity": "critical"
}
```

### Detectar Escaneo de Puertos (Nmap)
*Nota: Requiere analizar logs de firewall (UFW/IPTables), no implementado por defecto en auth.log, pero extensible.*

```json
{
 "id": "PORT_SCAN",
 "source": "log_syslog",
 "pattern": "UFW BLOCK",
 "threshold": 10,
 "window_seconds": 10
}
```
