"""
NAT traversal and peer discovery for Ghostline Signal.
Enables global P2P connections without port forwarding.
"""

import socket
import struct
import random
import time
import json
from typing import Optional, Tuple, Dict
import threading


class STUNClient:
    """STUN client for discovering public IP and port (RFC 5389)."""

    # Public STUN servers (use sparingly, consider self-hosting)
    STUN_SERVERS = [
        ('stun.l.google.com', 19302),
        ('stun1.l.google.com', 19302),
        ('stun2.l.google.com', 19302),
        ('stun3.l.google.com', 19302),
        ('stun4.l.google.com', 19302),
    ]

    # STUN message types
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101

    # STUN attributes
    MAPPED_ADDRESS = 0x0001
    XOR_MAPPED_ADDRESS = 0x0020

    # Magic cookie (RFC 5389)
    MAGIC_COOKIE = 0x2112A442

    @staticmethod
    def discover_public_address(local_port: int = 0) -> Optional[Tuple[str, int]]:
        """
        Discover public IP and port using STUN.
        Returns (public_ip, public_port) or None if failed.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        if local_port:
            sock.bind(('0.0.0.0', local_port))

        # Try multiple STUN servers
        for stun_server, stun_port in STUNClient.STUN_SERVERS:
            try:
                # Create STUN binding request
                transaction_id = random.randbytes(12)
                request = STUNClient._create_binding_request(transaction_id)

                # Send request
                sock.sendto(request, (stun_server, stun_port))

                # Receive response
                data, _ = sock.recvfrom(2048)

                # Parse response
                public_addr = STUNClient._parse_binding_response(data, transaction_id)
                if public_addr:
                    sock.close()
                    return public_addr

            except Exception as e:
                print(f"STUN request to {stun_server} failed: {e}")
                continue

        sock.close()
        return None

    @staticmethod
    def _create_binding_request(transaction_id: bytes) -> bytes:
        """Create STUN Binding Request message."""
        # Message type (Binding Request)
        message_type = struct.pack('>H', STUNClient.BINDING_REQUEST)
        # Message length (no attributes)
        message_length = struct.pack('>H', 0)
        # Magic cookie
        magic_cookie = struct.pack('>I', STUNClient.MAGIC_COOKIE)

        return message_type + message_length + magic_cookie + transaction_id

    @staticmethod
    def _parse_binding_response(data: bytes, transaction_id: bytes) -> Optional[Tuple[str, int]]:
        """Parse STUN Binding Response."""
        if len(data) < 20:
            return None

        # Verify message type
        msg_type = struct.unpack('>H', data[0:2])[0]
        if msg_type != STUNClient.BINDING_RESPONSE:
            return None

        # Verify transaction ID
        if data[8:20] != transaction_id:
            return None

        # Parse attributes
        offset = 20
        msg_length = struct.unpack('>H', data[2:4])[0]

        while offset < 20 + msg_length:
            if offset + 4 > len(data):
                break

            attr_type = struct.unpack('>H', data[offset:offset+2])[0]
            attr_length = struct.unpack('>H', data[offset+2:offset+4])[0]
            offset += 4

            if offset + attr_length > len(data):
                break

            # XOR-MAPPED-ADDRESS (preferred)
            if attr_type == STUNClient.XOR_MAPPED_ADDRESS:
                return STUNClient._parse_xor_mapped_address(data[offset:offset+attr_length], transaction_id)

            # MAPPED-ADDRESS (fallback)
            elif attr_type == STUNClient.MAPPED_ADDRESS:
                return STUNClient._parse_mapped_address(data[offset:offset+attr_length])

            offset += attr_length
            # Attributes are padded to 4-byte boundary
            if attr_length % 4:
                offset += 4 - (attr_length % 4)

        return None

    @staticmethod
    def _parse_xor_mapped_address(data: bytes, transaction_id: bytes) -> Optional[Tuple[str, int]]:
        """Parse XOR-MAPPED-ADDRESS attribute."""
        if len(data) < 8:
            return None

        family = data[1]
        if family != 0x01:  # IPv4 only for now
            return None

        # XOR port with most significant 16 bits of magic cookie
        xor_port = struct.unpack('>H', data[2:4])[0]
        port = xor_port ^ (STUNClient.MAGIC_COOKIE >> 16)

        # XOR IP with magic cookie
        xor_ip = struct.unpack('>I', data[4:8])[0]
        ip = xor_ip ^ STUNClient.MAGIC_COOKIE

        # Convert to dotted decimal
        ip_str = socket.inet_ntoa(struct.pack('>I', ip))

        return (ip_str, port)

    @staticmethod
    def _parse_mapped_address(data: bytes) -> Optional[Tuple[str, int]]:
        """Parse MAPPED-ADDRESS attribute."""
        if len(data) < 8:
            return None

        family = data[1]
        if family != 0x01:  # IPv4
            return None

        port = struct.unpack('>H', data[2:4])[0]
        ip = socket.inet_ntoa(data[4:8])

        return (ip, port)


class RendezvousClient:
    """
    Client for rendezvous server that enables peer discovery by device ID.
    Privacy-preserving: only stores device_id -> connection_info mapping temporarily.
    """

    def __init__(self, server_host: str = 'rendezvous.ghostline.local',
                 server_port: int = 8080):
        """Initialize rendezvous client."""
        self.server_host = server_host
        self.server_port = server_port
        self.registered = False
        self.heartbeat_thread = None
        self.running = False

    def register_device(self, device_id: str, public_ip: str, public_port: int,
                       local_ip: str = None, local_port: int = None) -> bool:
        """
        Register device with rendezvous server.
        Returns True if successful.
        """
        try:
            # Create registration message
            registration = {
                'action': 'register',
                'device_id': device_id,
                'public_addr': {'ip': public_ip, 'port': public_port},
                'local_addr': {'ip': local_ip, 'port': local_port} if local_ip else None,
                'timestamp': time.time()
            }

            # Send to rendezvous server
            response = self._send_request(registration)

            if response and response.get('status') == 'ok':
                self.registered = True
                self._start_heartbeat(device_id, public_ip, public_port, local_ip, local_port)
                return True

            return False

        except Exception as e:
            print(f"Registration failed: {e}")
            return False

    def lookup_device(self, device_id: str) -> Optional[Dict]:
        """
        Look up connection info for a device ID.
        Returns dict with public_addr and local_addr or None.
        """
        try:
            request = {
                'action': 'lookup',
                'device_id': device_id,
                'timestamp': time.time()
            }

            response = self._send_request(request)

            if response and response.get('status') == 'ok':
                return response.get('device_info')

            return None

        except Exception as e:
            print(f"Lookup failed: {e}")
            return None

    def send_connect_request(self, requester_id: str, target_id: str) -> Optional[Dict]:
        """
        Send a connection request to a target device.
        Returns target's device info if successful.
        """
        try:
            request = {
                'action': 'connect_request',
                'requester_id': requester_id,
                'target_id': target_id,
                'timestamp': time.time()
            }

            response = self._send_request(request)

            if response and response.get('status') == 'ok':
                return response.get('target_info')

            return None

        except Exception as e:
            print(f"Connect request failed: {e}")
            return None

    def get_connect_requests(self, device_id: str) -> list:
        """
        Get pending connection requests for this device.
        Returns list of requests with requester info.
        """
        try:
            request = {
                'action': 'get_connect_requests',
                'device_id': device_id,
                'timestamp': time.time()
            }

            response = self._send_request(request)

            if response and response.get('status') == 'ok':
                return response.get('requests', [])

            return []

        except Exception as e:
            print(f"Get connect requests failed: {e}")
            return []

    def clear_connect_request(self, target_id: str, requester_id: str) -> bool:
        """Clear a connection request after handling."""
        try:
            request = {
                'action': 'clear_connect_request',
                'target_id': target_id,
                'requester_id': requester_id,
                'timestamp': time.time()
            }

            response = self._send_request(request)
            return response and response.get('status') == 'ok'

        except Exception as e:
            print(f"Clear connect request failed: {e}")
            return False

    def unregister_device(self, device_id: str):
        """Unregister device from rendezvous server."""
        try:
            self.running = False
            if self.heartbeat_thread:
                self.heartbeat_thread.join(timeout=2)

            request = {
                'action': 'unregister',
                'device_id': device_id,
                'timestamp': time.time()
            }

            self._send_request(request)
            self.registered = False

        except Exception as e:
            print(f"Unregister failed: {e}")

    def _send_request(self, request: dict) -> Optional[dict]:
        """Send request to rendezvous server (HTTP-like protocol)."""
        try:
            # For now, use a simple HTTP POST-like request
            # In production, this should use HTTPS with certificate pinning
            import urllib.request
            import urllib.parse

            url = f"http://{self.server_host}:{self.server_port}/api"
            data = json.dumps(request).encode('utf-8')

            req = urllib.request.Request(url, data=data,
                                        headers={'Content-Type': 'application/json'})
            req.timeout = 5

            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))

        except Exception as e:
            # Rendezvous server might not be available - this is OK
            # The app can still work with manual IP entry
            print(f"Rendezvous server not available: {e}")
            return None

    def _start_heartbeat(self, device_id: str, public_ip: str, public_port: int,
                        local_ip: str = None, local_port: int = None):
        """Start heartbeat to keep registration alive."""
        self.running = True

        def heartbeat_loop():
            while self.running:
                time.sleep(60)  # Heartbeat every 60 seconds
                if not self.running:
                    break

                try:
                    heartbeat = {
                        'action': 'heartbeat',
                        'device_id': device_id,
                        'public_addr': {'ip': public_ip, 'port': public_port},
                        'local_addr': {'ip': local_ip, 'port': local_port} if local_ip else None,
                        'timestamp': time.time()
                    }
                    self._send_request(heartbeat)
                except:
                    pass

        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()


class HolePuncher:
    """Implements UDP/TCP hole punching for NAT traversal."""

    @staticmethod
    def punch_hole_tcp(local_port: int, remote_ip: str, remote_port: int,
                      timeout: int = 10) -> Optional[socket.socket]:
        """
        Attempt TCP hole punching.
        Returns connected socket or None.
        """
        # TCP hole punching is more complex and less reliable than UDP
        # This is a simplified version
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', local_port))
            sock.settimeout(timeout)

            # Attempt to connect
            sock.connect((remote_ip, remote_port))
            return sock

        except Exception as e:
            print(f"Hole punching failed: {e}")
            return None

    @staticmethod
    def simultaneous_connect(local_port: int, remote_ip: str, remote_port: int) -> Optional[socket.socket]:
        """
        Attempt simultaneous TCP connect for hole punching.
        Both peers must attempt at roughly the same time.
        """
        # This requires coordination - implemented in connection broker
        pass
