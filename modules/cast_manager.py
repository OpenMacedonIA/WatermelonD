import time
import logging
import threading

logger = logging.getLogger("NeoCast")

try:
    import pychromecast
    CAST_AVAILABLE = True
except ImportError:
    logger.warning("pychromecast not installed. Casting disabled.")
    CAST_AVAILABLE = False

class CastManager:
    def __init__(self):
        self.casts = {}
        self.browser = None
        self.is_scanning = False
        
    def start_discovery(self):
        """Inicia el descubrimiento de dispositivos en segundo plano."""
        if not CAST_AVAILABLE:
            return
            
        logger.info("Starting Chromecast discovery...")
        # Descubrir dispositivos
        self.casts = {c.name: c for c in pychromecast.get_chromecasts()[0]}
        logger.info(f"Discovered {len(self.casts)} cast devices: {list(self.casts.keys())}")

    def get_devices(self):
        """Devuelve una lista de nombres de dispositivos descubiertos."""
        return list(self.casts.keys())

    def play_media(self, device_name, media_url, content_type="video/mp4"):
        """Reproduce multimedia en un dispositivo específico."""
        if not CAST_AVAILABLE:
            return False, "Módulo Cast no disponible."

        # Búsqueda difusa del nombre del dispositivo si es necesario, por ahora coincidencia exacta o parcial
        target_cast = None
        
        # Coincidencia directa
        if device_name in self.casts:
            target_cast = self.casts[device_name]
        else:
            # Coincidencia parcial
            for name, cast in self.casts.items():
                if device_name.lower() in name.lower():
                    target_cast = cast
                    break
        
        if not target_cast:
            # Refrescar descubrimiento por si acaso
            self.start_discovery()
            return False, f"No encuentro el dispositivo '{device_name}'."

        try:
            target_cast.wait()
            mc = target_cast.media_controller
            mc.play_media(media_url, content_type)
            mc.block_until_active()
            return True, f"Reproduciendo en {target_cast.name}."
        except Exception as e:
            logger.error(f"Error casting to {device_name}: {e}")
            return False, f"Error al conectar con {device_name}."

    def stop_media(self, device_name=None):
        """Detiene multimedia en un dispositivo (o todos si es None)."""
        if not CAST_AVAILABLE:
            return False
            
        if device_name:
             # Lógica similar a play_media para encontrar dispositivo
             pass
        else:
            # Detener todos
            for cast in self.casts.values():
                try:
                    cast.wait()
                    cast.media_controller.stop()
                except:
                    pass
            return True, "Reproducción detenida en todos los dispositivos."

    def broadcast_media(self, media_url, content_type="audio/mp3"):
        """
        Reproduce multimedia en TODOS los dispositivos descubiertos.
        Nota: Esto no está perfectamente sincronizado (posible desvío de 10-500ms).
        Para sincronización perfecta, usar Grupos de Google Home y apuntar al nombre del grupo.
        """
        if not CAST_AVAILABLE or not self.casts:
            self.start_discovery()
            
        success_count = 0
        for name, cast in self.casts.items():
            try:
                cast.wait()
                mc = cast.media_controller
                mc.play_media(media_url, content_type)
                mc.block_until_active()
                success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {name}: {e}")
                
        if success_count > 0:
            return True, f"Transmitiendo en {success_count} dispositivos."
        return False, "No se pudo transmitir en ningún dispositivo."
