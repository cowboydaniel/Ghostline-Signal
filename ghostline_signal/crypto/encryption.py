"""
Message encryption and decryption for Ghostline Signal.
Implements end-to-end encryption with authenticated encryption.
"""

import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


class MessageEncryption:
    """Handles message encryption and decryption."""

    @staticmethod
    def encrypt_message(plaintext: bytes, session_key: bytes) -> bytes:
        """
        Encrypt message using AES-256-GCM with the session key.
        Returns: nonce (12 bytes) + ciphertext + tag (16 bytes)
        """
        aesgcm = AESGCM(session_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM

        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Return nonce + ciphertext (ciphertext includes auth tag)
        return nonce + ciphertext

    @staticmethod
    def decrypt_message(encrypted_data: bytes, session_key: bytes) -> bytes:
        """
        Decrypt message using AES-256-GCM with the session key.
        Expects: nonce (12 bytes) + ciphertext + tag (16 bytes)
        """
        if len(encrypted_data) < 13:  # Minimum: 12-byte nonce + 1 byte
            raise ValueError("Encrypted data too short")

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        aesgcm = AESGCM(session_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext

    @staticmethod
    def add_padding(data: bytes, block_size: int = 256) -> bytes:
        """
        Add padding to obscure message length.
        Uses PKCS7-style padding up to nearest block_size.
        """
        current_len = len(data)
        target_len = ((current_len // block_size) + 1) * block_size
        padding_len = target_len - current_len

        # Add length prefix (4 bytes) + data + padding
        return struct.pack('>I', current_len) + data + (bytes([padding_len]) * padding_len)

    @staticmethod
    def remove_padding(padded_data: bytes) -> bytes:
        """Remove padding and extract original message."""
        if len(padded_data) < 5:  # Minimum: 4-byte length + 1 byte
            raise ValueError("Padded data too short")

        original_len = struct.unpack('>I', padded_data[:4])[0]
        return padded_data[4:4 + original_len]
