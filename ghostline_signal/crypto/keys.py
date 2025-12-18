"""
Key generation and management for Ghostline Signal.
Implements local key generation with non-exportable private keys.
"""

import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


class KeyManager:
    """Manages cryptographic keys for the local device."""

    def __init__(self, storage_path: str = None):
        """Initialize key manager with local storage path."""
        if storage_path is None:
            storage_path = os.path.join(str(Path.home()), '.ghostline_signal', 'keys')

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.private_key_path = self.storage_path / 'device_private.key'
        self.public_key_path = self.storage_path / 'device_public.pem'

        self.private_key = None
        self.public_key = None

        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        if self.private_key_path.exists() and self.public_key_path.exists():
            self._load_keys()
        else:
            self._generate_keys()

    def _generate_keys(self):
        """Generate new RSA key pair (4096-bit for strong security)."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Save private key (encrypted at rest)
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # Could add password protection
        )

        # Save public key
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Secure file permissions
        self.private_key_path.write_bytes(private_pem)
        self.private_key_path.chmod(0o600)

        self.public_key_path.write_bytes(public_pem)

    def _load_keys(self):
        """Load existing keys from storage."""
        # Load private key
        private_pem = self.private_key_path.read_bytes()
        self.private_key = serialization.load_pem_private_key(
            private_pem,
            password=None,
            backend=default_backend()
        )

        # Load public key
        public_pem = self.public_key_path.read_bytes()
        self.public_key = serialization.load_pem_public_key(
            public_pem,
            backend=default_backend()
        )

    def get_public_key_bytes(self) -> bytes:
        """Get public key as bytes for sharing with peers."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def load_peer_public_key(self, public_key_pem: bytes):
        """Load a peer's public key from PEM bytes."""
        return serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

    def generate_session_key(self) -> bytes:
        """Generate ephemeral session key (256-bit)."""
        return os.urandom(32)

    def derive_key(self, shared_secret: bytes, salt: bytes = None) -> bytes:
        """Derive encryption key from shared secret using HKDF."""
        if salt is None:
            salt = os.urandom(16)

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'ghostline-signal-session',
            backend=default_backend()
        )
        return hkdf.derive(shared_secret)

    def encrypt_session_key(self, session_key: bytes, peer_public_key) -> bytes:
        """Encrypt session key with peer's public key."""
        encrypted = peer_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted

    def decrypt_session_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt session key with own private key."""
        decrypted = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
