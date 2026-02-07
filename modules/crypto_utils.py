"""
Password encryption utilities using Fernet (AES-128).
Replaces Base64 obfuscation with real encryption.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging

logger = logging.getLogger("CryptoUtils")


class PasswordCrypto:
    """
    Encrypts/decrypts passwords using Fernet (symmetric encryption).
    Uses machine-specific key derived from /etc/machine-id.
    """
    
    def __init__(self):
        self._fernet = None
        try:
            key = self._get_encryption_key()
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize crypto: {e}")
            self._fernet = None
    
    def _get_encryption_key(self):
        """
        Generate encryption key based on machine ID.
        This makes passwords non-portable between machines.
        """
        try:
            # Try to get machine-id (Linux)
            with open('/etc/machine-id', 'r', encoding='utf-8') as f:
                machine_id = f.read().strip()
        except FileNotFoundError:
            # Fallback for systems without machine-id (macOS, BSD)
            try:
                machine_id = os.uname().nodename + os.uname().machine
            except:
                # Last resort fallback
                machine_id = "watermelond_default_id"
                logger.warning("Could not get machine ID, using default (less secure)")
        
        # Derive key using PBKDF2
        salt = b'watermelond_ssh_password_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key_bytes = kdf.derive(machine_id.encode())
        key = base64.urlsafe_b64encode(key_bytes)
        
        return key
    
    def encrypt(self, plaintext):
        """
        Encrypt a password string.
        Returns: "FERNET:encrypted_data" or None on error
        """
        if not plaintext:
            return None
        
        if not self._fernet:
            logger.error("Crypto not initialized, cannot encrypt")
            return self._fallback_obfuscate(plaintext)
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return f"FERNET:{encrypted.decode()}"
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return self._fallback_obfuscate(plaintext)
    
    def decrypt(self, encrypted_text):
        """
        Decrypt a password string.
        Supports both FERNET: and legacy ENC: (Base64) formats.
        Returns: decrypted plaintext or original text on error
        """
        if not encrypted_text:
            return None
        
        # Handle Fernet encryption
        if encrypted_text.startswith("FERNET:"):
            if not self._fernet:
                logger.error("Crypto not initialized, cannot decrypt")
                return None
            
            try:
                token = encrypted_text.split("FERNET:")[1]
                decrypted = self._fernet.decrypt(token.encode())
                return decrypted.decode()
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return None
        
        # Handle legacy Base64 obfuscation (backwards compatibility)
        elif encrypted_text.startswith("ENC:"):
            try:
                raw = encrypted_text.split("ENC:")[1]
                decoded = base64.b64decode(raw).decode()
                logger.warning("Found legacy Base64 password - consider re-encrypting with Fernet")
                return decoded
            except Exception as e:
                logger.error(f"Base64 decode failed: {e}")
                return None
        
        # Plain text (legacy)
        else:
            logger.warning("Found plaintext password - should be encrypted")
            return encrypted_text
    
    def _fallback_obfuscate(self, text):
        """Fallback to Base64 if Fernet fails."""
        try:
            encoded = base64.b64encode(text.encode()).decode()
            logger.warning("Using Base64 fallback (less secure)")
            return f"ENC:{encoded}"
        except:
            return None


# Global instance
_crypto_instance = None

def get_crypto():
    """Get singleton PasswordCrypto instance."""
    global _crypto_instance
    if _crypto_instance is None:
        _crypto_instance = PasswordCrypto()
    return _crypto_instance
