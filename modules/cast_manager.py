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
        """Starts discovering devices in background."""
        if not CAST_AVAILABLE:
            return
            
        logger.info("Starting Chromecast discovery...")
        # Discover devices
        self.casts = {c.name: c for c in pychromecast.get_chromecasts()[0]}
        logger.info(f"Discovered {len(self.casts)} cast devices: {list(self.casts.keys())}")

    def get_devices(self):
        """Returns a list of discovered device names."""
        return list(self.casts.keys())

    def play_media(self, device_name, media_url, content_type="video/mp4"):
        """Plays media on a specific device."""
        if not CAST_AVAILABLE:
            return False, "Módulo Cast no disponible."

        # Fuzzy match device name if needed, for now exact match or partial
        target_cast = None
        
        # Direct match
        if device_name in self.casts:
            target_cast = self.casts[device_name]
        else:
            # Partial match
            for name, cast in self.casts.items():
                if device_name.lower() in name.lower():
                    target_cast = cast
                    break
        
        if not target_cast:
            # Refresh discovery just in case
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
        """Stops media on a device (or all if None)."""
        if not CAST_AVAILABLE:
            return False
            
        if device_name:
             # Logic similar to play_media for finding device
             pass
        else:
            # Stop all
            for cast in self.casts.values():
                try:
                    cast.wait()
                    cast.media_controller.stop()
                except:
                    pass
            return True, "Reproducción detenida en todos los dispositivos."

    def broadcast_media(self, media_url, content_type="audio/mp3"):
        """
        Plays media on ALL discovered devices.
        Note: This is not perfectly synchronized (10-500ms drift possible).
        For perfect sync, use Google Home Groups and target the group name.
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
