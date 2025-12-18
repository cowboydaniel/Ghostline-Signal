"""
Device identity management for Ghostline Signal.
Identity is bound to the device, not a person or account.
"""

import hashlib
import uuid
from typing import Optional
from pathlib import Path
import json


class DeviceIdentity:
    """Manages the local device identity."""

    def __init__(self, storage_path: str = None):
        """Initialize device identity."""
        if storage_path is None:
            storage_path = Path.home() / '.ghostline_signal' / 'identity.json'
        else:
            storage_path = Path(storage_path)

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.identity_path = storage_path

        self.device_id: Optional[str] = None
        self.device_name: Optional[str] = None
        self.device_fingerprint: Optional[str] = None

        self._load_or_create_identity()

    def _load_or_create_identity(self):
        """Load existing identity or create new one."""
        if self.identity_path.exists():
            self._load_identity()
        else:
            self._create_identity()

    def _create_identity(self):
        """Create a new device identity."""
        # Generate unique device ID
        self.device_id = str(uuid.uuid4())

        # Default device name
        import socket
        hostname = socket.gethostname()
        self.device_name = f"Ghostline-{hostname}"

        # Generate device fingerprint
        self.device_fingerprint = self._generate_fingerprint()

        self._save_identity()

    def _load_identity(self):
        """Load existing identity from storage."""
        with open(self.identity_path, 'r') as f:
            data = json.load(f)

        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_fingerprint = data.get('device_fingerprint')

    def _save_identity(self):
        """Save identity to storage."""
        data = {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_fingerprint': self.device_fingerprint
        }

        with open(self.identity_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Secure file permissions
        self.identity_path.chmod(0o600)

    def _generate_fingerprint(self) -> str:
        """Generate a device fingerprint based on device ID."""
        hash_obj = hashlib.sha256(self.device_id.encode())
        return hash_obj.hexdigest()[:16].upper()

    def get_device_id(self) -> str:
        """Get the device ID."""
        return self.device_id

    def get_device_name(self) -> str:
        """Get the device name."""
        return self.device_name

    def set_device_name(self, name: str):
        """Set a custom device name."""
        self.device_name = name
        self._save_identity()

    def get_device_fingerprint(self) -> str:
        """Get the device fingerprint for verification."""
        return self.device_fingerprint

    def get_identity_summary(self) -> dict:
        """Get a summary of the device identity."""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'fingerprint': self.device_fingerprint
        }

    @staticmethod
    def format_fingerprint(fingerprint: str) -> str:
        """Format fingerprint for display (e.g., XXXX-XXXX-XXXX-XXXX)."""
        if len(fingerprint) == 16:
            return '-'.join([fingerprint[i:i+4] for i in range(0, 16, 4)])
        return fingerprint
