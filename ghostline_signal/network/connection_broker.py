"""
Connection broker for Ghostline Signal.
Handles automatic peer discovery and NAT traversal using device IDs.
"""

import socket
from typing import Optional, Callable, Dict
from .nat_traversal import STUNClient, RendezvousClient, HolePuncher
from .p2p import P2PNode


class ConnectionBroker:
    """
    Manages automatic peer connections using device IDs.
    Handles NAT traversal, peer discovery, and connection establishment.
    """

    def __init__(self, p2p_node: P2PNode, device_id: str,
                 use_rendezvous: bool = True,
                 rendezvous_server: str = None):
        """
        Initialize connection broker.

        Args:
            p2p_node: The P2P node instance
            device_id: This device's unique ID
            use_rendezvous: Whether to use rendezvous server for discovery
            rendezvous_server: Custom rendezvous server (format: host:port)
        """
        self.p2p_node = p2p_node
        self.device_id = device_id
        self.use_rendezvous = use_rendezvous

        # Public address discovered via STUN
        self.public_ip: Optional[str] = None
        self.public_port: Optional[int] = None

        # Local address
        self.local_ip: Optional[str] = None
        self.local_port: Optional[int] = None

        # Rendezvous client
        if use_rendezvous:
            if rendezvous_server:
                host, port = rendezvous_server.split(':')
                self.rendezvous = RendezvousClient(host, int(port))
            else:
                # Default to built-in fallback
                self.rendezvous = RendezvousClient('127.0.0.1', 8080)
        else:
            self.rendezvous = None

        self.status_callback: Optional[Callable] = None

    def initialize(self) -> bool:
        """
        Initialize connection broker.
        Discovers public IP, registers with rendezvous server.
        Returns True if successful.
        """
        # Get local address
        host, port = self.p2p_node.get_address()
        self.local_ip = self._get_local_ip()
        self.local_port = port

        self._notify_status(f"Local address: {self.local_ip}:{self.local_port}")

        # Discover public IP using STUN
        self._notify_status("Discovering public IP address...")
        public_addr = STUNClient.discover_public_address(self.local_port)

        if public_addr:
            self.public_ip, self.public_port = public_addr
            self._notify_status(f"Public address: {self.public_ip}:{self.public_port}")
        else:
            self._notify_status("Could not discover public IP (STUN failed)")
            # Use local IP as fallback
            self.public_ip = self.local_ip
            self.public_port = self.local_port

        # Register with rendezvous server
        if self.use_rendezvous and self.rendezvous:
            self._notify_status("Registering with rendezvous server...")
            success = self.rendezvous.register_device(
                self.device_id,
                self.public_ip,
                self.public_port,
                self.local_ip,
                self.local_port
            )

            if success:
                self._notify_status("Registered with rendezvous server")
            else:
                self._notify_status("Rendezvous server not available (manual connection only)")

        return True

    def connect_by_device_id(self, peer_device_id: str) -> Optional[str]:
        """
        Connect to a peer using their device ID.
        Handles peer discovery and NAT traversal automatically.

        Returns peer_id (host:port) if successful, None otherwise.
        """
        self._notify_status(f"Looking up device: {peer_device_id}")

        # Try rendezvous server first
        if self.use_rendezvous and self.rendezvous:
            device_info = self.rendezvous.lookup_device(peer_device_id)

            if device_info:
                return self._connect_to_device_info(device_info)

        self._notify_status("Peer not found on rendezvous server")
        return None

    def _connect_to_device_info(self, device_info: Dict) -> Optional[str]:
        """Connect to peer using discovered device info."""
        public_addr = device_info.get('public_addr', {})
        local_addr = device_info.get('local_addr', {})

        # Try local address first (if on same network)
        if local_addr and local_addr.get('ip'):
            self._notify_status(f"Trying local address: {local_addr['ip']}:{local_addr['port']}")
            peer_id = self._try_connect(local_addr['ip'], local_addr['port'])
            if peer_id:
                return peer_id

        # Try public address
        if public_addr and public_addr.get('ip'):
            self._notify_status(f"Trying public address: {public_addr['ip']}:{public_addr['port']}")
            peer_id = self._try_connect(public_addr['ip'], public_addr['port'])
            if peer_id:
                return peer_id

        # Try hole punching as last resort
        if public_addr and public_addr.get('ip'):
            self._notify_status("Attempting NAT traversal (hole punching)...")
            peer_id = self._try_hole_punching(public_addr['ip'], public_addr['port'])
            if peer_id:
                return peer_id

        return None

    def _try_connect(self, host: str, port: int, timeout: int = 5) -> Optional[str]:
        """Try to connect to a peer."""
        try:
            peer_id = self.p2p_node.connect_to_peer(host, port)
            return peer_id
        except Exception as e:
            return None

    def _try_hole_punching(self, remote_ip: str, remote_port: int) -> Optional[str]:
        """Try hole punching to establish connection."""
        # This is a simplified version
        # Full implementation would require coordination via rendezvous server
        try:
            sock = HolePuncher.punch_hole_tcp(self.local_port, remote_ip, remote_port)
            if sock:
                # Connection established via hole punching
                # Would need to integrate with P2PNode
                sock.close()
                return f"{remote_ip}:{remote_port}"
        except:
            pass

        return None

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def _notify_status(self, message: str):
        """Notify status change."""
        print(f"[ConnectionBroker] {message}")
        if self.status_callback:
            self.status_callback(message)

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates."""
        self.status_callback = callback

    def shutdown(self):
        """Shutdown connection broker."""
        if self.rendezvous:
            self.rendezvous.unregister_device(self.device_id)

    def get_connection_info(self) -> Dict:
        """Get connection information for sharing."""
        return {
            'device_id': self.device_id,
            'local': {
                'ip': self.local_ip,
                'port': self.local_port
            },
            'public': {
                'ip': self.public_ip,
                'port': self.public_port
            }
        }
