import os
import time
import sys
import argparse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WhisperOptimizer")

def check_dependencies():
    try:
        import faster_whisper
        return True
    except ImportError:
        logger.error("La librería 'faster-whisper' no está instalada.")
        logger.info("Por favor, instálala con: pip install faster-whisper")
        return False

def benchmark_model(model_size, device="cpu", compute_type="int8"):
    from faster_whisper import WhisperModel

    logger.info(f"--- Iniciando Benchmark: {model_size} ({compute_type}) en {device} ---")
    
    try:
        # 1. Cargar Modelo (esto descargará y convertirá si es necesario)
        start_load = time.time()
        model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root="whisper_models")
        load_time = time.time() - start_load
        logger.info(f"Modelo cargado en {load_time:.2f} segundos.")

        # 2. Generar audio de prueba (silencio/ruido sintético no sirve para transcripción real, 
        # pero sirve para medir velocidad de inferencia bruta si el modelo procesa algo).
        # Mejor usamos un archivo real si existe, o advertimos.
        
        # Para un benchmark sintético rápido, podemos intentar transcribir un archivo dummy si existiera,
        # pero sin archivo de audio es difícil. 
        # Vamos a asumir que el usuario tiene un archivo o usamos uno del sistema si encontramos.
        
        audio_file = "tests/samples/test_audio.wav" # Path hipotético
        if not os.path.exists(audio_file):
            # Crear un wav dummy de 5 segundos de ruido blanco
            import wave
            import random
            import struct
            
            logger.info("Generando archivo de audio de prueba (5s de ruido)...")
            audio_file = "temp_benchmark.wav"
            with wave.open(audio_file, 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(16000)
                for _ in range(16000 * 5):
                    value = random.randint(-32767, 32767)
                    data = struct.pack('<h', value)
                    f.writeframesraw(data)
        
        # 3. Transcribir
        logger.info("Transcribiendo audio de prueba (5 segundos)...")
        start_transcribe = time.time()
        segments, info = model.transcribe(audio_file, beam_size=5)
        
        # Consumir generador
        count = 0
        for segment in segments:
            count += 1
            
        total_time = time.time() - start_transcribe
        audio_duration = 5.0 # Sabemos que generamos 5s
        
        rtf = total_time / audio_duration
        
        logger.info(f"Tiempo de transcripción: {total_time:.2f}s")
        logger.info(f"Real Time Factor (RTF): {rtf:.2f}")
        
        if rtf < 1.0:
            logger.info("✅ RESULTADO: El modelo es MÁS RÁPIDO que el tiempo real. Apto para uso.")
        else:
            logger.warning("⚠️ RESULTADO: El modelo es MÁS LENTO que el tiempo real. Puede haber latencia.")
            
        # Limpieza
        if audio_file == "temp_benchmark.wav":
            os.remove(audio_file)
            
        return rtf

    except Exception as e:
        logger.error(f"Error durante el benchmark: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Herramienta de Optimización de Whisper para OpenKompai")
    parser.add_argument("--model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large-v3"], help="Tamaño del modelo a probar")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="Dispositivo de inferencia")
    parser.add_argument("--quantization", type=str, default="int8", choices=["int8", "float16", "float32"], help="Tipo de cuantización")
    parser.add_argument("--auto-configure", action="store_true", help="Actualizar config.json automáticamente si el RTF es bueno")
    
    args = parser.parse_args()
    
    if not check_dependencies():
        sys.exit(1)
        
    print(f"\nOptimización de Whisper para OpenKompai Nano")
    print("============================================")
    print(f"Modelo: {args.model}")
    print(f"Hardware: {args.device}")
    print(f"Precisión: {args.quantization}")
    print("--------------------------------------------")
    
    rtf = benchmark_model(args.model, args.device, args.quantization)
    
    if rtf:
        print("\nResumen:")
        print(f"Modelo guardado en: ./whisper_models")
        print(f"RTF: {rtf:.3f} (Menor es mejor)")
        
        if args.auto_configure and rtf < 1.0:
            update_config(args.model, args.device, args.quantization)
        elif args.auto_configure:
            print("⚠️ No se actualizó la configuración porque el rendimiento no es óptimo (RTF > 1.0).")

def update_config(model, device, compute_type):
    import json
    config_path = "config.json"
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
            
        if 'stt' not in config:
            config['stt'] = {}
            
        config['stt']['engine'] = 'hybrid'
        config['stt']['whisper_model'] = model
        config['stt']['whisper_device'] = device
        config['stt']['whisper_compute'] = compute_type
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        print(f"✅ config.json actualizado: engine='hybrid', model='{model}'")
        
    except Exception as e:
        print(f"❌ Error actualizando config.json: {e}")

if __name__ == "__main__":
    main()
