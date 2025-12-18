"""
Traffic obfuscation for Ghostline Signal.
Implements randomized packet sizes, variable timing, and indistinguishable payloads.
"""

import os
import time
import random
from typing import List


class TrafficObfuscator:
    """Obfuscates network traffic to prevent pattern analysis."""

    # Packet size range for obfuscation
    MIN_PACKET_SIZE = 128
    MAX_PACKET_SIZE = 8192

    # Timing jitter range (milliseconds)
    MIN_JITTER_MS = 10
    MAX_JITTER_MS = 500

    @staticmethod
    def obfuscate_payload(data: bytes) -> List[bytes]:
        """
        Split data into randomized chunks to obscure message boundaries.
        Returns list of obfuscated packets.
        """
        packets = []
        offset = 0
        data_len = len(data)

        while offset < data_len:
            # Random packet size
            packet_size = random.randint(
                TrafficObfuscator.MIN_PACKET_SIZE,
                TrafficObfuscator.MAX_PACKET_SIZE
            )

            # Extract chunk
            chunk = data[offset:offset + packet_size]
            offset += len(chunk)

            # Pad to random size if needed
            if len(chunk) < packet_size and offset >= data_len:
                # Last packet - pad to random size
                padding_size = packet_size - len(chunk)
                chunk = chunk + os.urandom(padding_size)

            packets.append(chunk)

        # Add random decoy packets occasionally
        if random.random() < 0.3:  # 30% chance
            decoy_count = random.randint(1, 3)
            for _ in range(decoy_count):
                decoy_size = random.randint(
                    TrafficObfuscator.MIN_PACKET_SIZE,
                    TrafficObfuscator.MAX_PACKET_SIZE
                )
                packets.insert(random.randint(0, len(packets)), os.urandom(decoy_size))

        return packets

    @staticmethod
    def add_timing_jitter() -> float:
        """
        Generate random timing jitter to obscure message patterns.
        Returns delay in seconds.
        """
        jitter_ms = random.uniform(
            TrafficObfuscator.MIN_JITTER_MS,
            TrafficObfuscator.MAX_JITTER_MS
        )
        return jitter_ms / 1000.0

    @staticmethod
    def create_cover_traffic(size: int = None) -> bytes:
        """
        Generate cover traffic (random data) to blend with real messages.
        """
        if size is None:
            size = random.randint(
                TrafficObfuscator.MIN_PACKET_SIZE,
                TrafficObfuscator.MAX_PACKET_SIZE
            )
        return os.urandom(size)

    @staticmethod
    def wrap_message(message: bytes, message_type: int = 0x01) -> bytes:
        """
        Wrap message with metadata in a way that looks like generic data.
        Format: [random_header (16 bytes)] [type (1 byte)] [length (4 bytes)] [message] [random_footer (variable)]
        """
        import struct

        header = os.urandom(16)
        length_bytes = struct.pack('>I', len(message))
        type_byte = bytes([message_type])

        # Random footer size
        footer_size = random.randint(16, 128)
        footer = os.urandom(footer_size)

        return header + type_byte + length_bytes + message + footer

    @staticmethod
    def unwrap_message(wrapped: bytes) -> tuple:
        """
        Unwrap message from obfuscated format.
        Returns: (message_type, message_data)
        """
        import struct

        if len(wrapped) < 21:  # Minimum: 16 + 1 + 4
            raise ValueError("Wrapped message too short")

        message_type = wrapped[16]
        message_length = struct.unpack('>I', wrapped[17:21])[0]

        message_data = wrapped[21:21 + message_length]

        return message_type, message_data
