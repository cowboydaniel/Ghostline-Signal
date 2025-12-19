"""
Connection broker for Ghostline Signal.
Handles automatic peer discovery and NAT traversal using device IDs.
"""

import socket
import time
import threading
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
        self.connection_callback: Optional[Callable] = None

        # Polling for incoming connection requests
        self.running = False
        self.poll_thread: Optional[threading.Thread] = None
        self.poll_interval = 2  # Check every 2 seconds

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
                # Start polling for incoming connection requests
                self._start_request_polling()
            else:
                self._notify_status("Rendezvous server not available")

        return True

    def _start_request_polling(self):
        """Start polling for incoming connection requests."""
        if self.poll_thread and self.poll_thread.is_alive():
            return

        self.running = True

        def poll_loop():
            while self.running:
                try:
                    self._check_incoming_requests()
                except Exception as e:
                    print(f"[ConnectionBroker] Poll error: {e}")
                time.sleep(self.poll_interval)

        self.poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self.poll_thread.start()
        self._notify_status("Listening for incoming connection requests")

    def _check_incoming_requests(self):
        """Check for and handle incoming connection requests."""
        if not self.rendezvous:
            return

        requests = self.rendezvous.get_connect_requests(self.device_id)

        for req in requests:
            requester_id = req.get('requester_id')
            requester_info = req.get('requester_info', {})

            if not requester_id:
                continue

            self._notify_status(f"Incoming connection request from {requester_id[:8]}...")

            # Try to connect back to the requester
            peer_id = self._connect_to_device_info(requester_info)

            if peer_id:
                self._notify_status(f"Connected to {requester_id[:8]}...")
                # Clear the request
                self.rendezvous.clear_connect_request(self.device_id, requester_id)
                # Notify callback if set
                if self.connection_callback:
                    self.connection_callback(peer_id, requester_id)

    def connect_by_device_id(self, peer_device_id: str) -> Optional[str]:
        """
        Connect to a peer using their device ID.
        Handles peer discovery and NAT traversal automatically.

        Returns peer_id (host:port) if successful, None otherwise.
        """
        self._notify_status(f"Looking up device: {peer_device_id[:8]}...")

        if not self.use_rendezvous or not self.rendezvous:
            self._notify_status("Rendezvous server not configured")
            return None

        # Step 1: Send a connection request so the peer knows we want to connect
        # This enables the peer to also try connecting to us (for NAT traversal)
        self._notify_status("Sending connection request...")
        target_info = self.rendezvous.send_connect_request(self.device_id, peer_device_id)

        if not target_info:
            self._notify_status("Peer not found on rendezvous server")
            return None

        # Step 2: Try to connect to the peer
        # While we're doing this, the peer may also be trying to connect to us
        self._notify_status("Attempting connection...")
        peer_id = self._connect_to_device_info(target_info)

        if peer_id:
            # Clear our request since we connected
            self.rendezvous.clear_connect_request(peer_device_id, self.device_id)
            return peer_id

        # Step 3: If direct connection failed, wait briefly for peer to connect to us
        # The peer should have seen our request and may be connecting back
        self._notify_status("Waiting for peer to establish connection...")
        initial_peers = set(self.p2p_node.get_peer_list())

        for i in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            # Check if a new peer connected to us
            current_peers = set(self.p2p_node.get_peer_list())
            new_peers = current_peers - initial_peers

            if new_peers:
                # A new peer appeared - it might be our target
                new_peer_id = next(iter(new_peers))
                self._notify_status(f"Peer connected: {new_peer_id}")
                return new_peer_id

            if i == 4:
                self._notify_status("Still waiting for peer...")

        self._notify_status("Connection failed - peer may be behind strict NAT")
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
                # Integrate the socket with P2PNode
                peer_id = f"{remote_ip}:{remote_port}"
                self.p2p_node.add_connected_socket(sock, peer_id)
                return peer_id
        except Exception as e:
            self._notify_status(f"Hole punching failed: {e}")

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
        self.running = False
        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join(timeout=3)
        if self.rendezvous:
            self.rendezvous.unregister_device(self.device_id)

    def set_connection_callback(self, callback: Callable):
        """Set callback for new incoming connections."""
        self.connection_callback = callback

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
