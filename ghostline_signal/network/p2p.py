"""
P2P networking layer for Ghostline Signal.
Implements peer-to-peer connections with no central server.
"""

import socket
import threading
import time
import struct
from typing import Callable, Optional, Dict
from queue import Queue
from .obfuscation import TrafficObfuscator


class P2PNode:
    """Peer-to-peer network node."""

    def __init__(self, host: str = '0.0.0.0', port: int = 0):
        """Initialize P2P node."""
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.peers: Dict[str, socket.socket] = {}
        self.message_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        self.obfuscator = TrafficObfuscator()
        self.message_queue = Queue()
        self._lock = threading.Lock()

    def start(self):
        """Start the P2P node server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))

        # Get assigned port if port was 0
        self.port = self.server_socket.getsockname()[1]

        self.server_socket.listen(5)
        self.running = True

        # Start server thread
        server_thread = threading.Thread(target=self._accept_connections, daemon=True)
        server_thread.start()

    def stop(self):
        """Stop the P2P node."""
        self.running = False

        # Close all peer connections
        with self._lock:
            for peer_id, sock in list(self.peers.items()):
                try:
                    sock.close()
                except:
                    pass
            self.peers.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def _accept_connections(self):
        """Accept incoming peer connections."""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, address = self.server_socket.accept()

                # Handle connection in separate thread
                peer_id = f"{address[0]}:{address[1]}"
                with self._lock:
                    self.peers[peer_id] = client_socket

                thread = threading.Thread(
                    target=self._handle_peer,
                    args=(peer_id, client_socket),
                    daemon=True
                )
                thread.start()

                if self.connection_callback:
                    self.connection_callback(peer_id, 'connected')

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")

    def connect_to_peer(self, host: str, port: int, timeout: int = 5) -> str:
        """Connect to a remote peer."""
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(timeout)
            peer_socket.connect((host, port))

            peer_id = f"{host}:{port}"
            with self._lock:
                self.peers[peer_id] = peer_socket

            # Start handling this peer
            thread = threading.Thread(
                target=self._handle_peer,
                args=(peer_id, peer_socket),
                daemon=True
            )
            thread.start()

            if self.connection_callback:
                self.connection_callback(peer_id, 'connected')

            return peer_id

        except Exception as e:
            raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")

    def add_connected_socket(self, sock: socket.socket, peer_id: str) -> str:
        """Add an already-connected socket as a peer (e.g., from hole punching)."""
        with self._lock:
            self.peers[peer_id] = sock

        # Start handling this peer
        thread = threading.Thread(
            target=self._handle_peer,
            args=(peer_id, sock),
            daemon=True
        )
        thread.start()

        if self.connection_callback:
            self.connection_callback(peer_id, 'connected')

        return peer_id

    def _handle_peer(self, peer_id: str, sock: socket.socket):
        """Handle communication with a peer."""
        buffer = b''

        while self.running:
            try:
                # Receive data
                sock.settimeout(1.0)
                data = sock.recv(4096)

                if not data:
                    break

                buffer += data

                # Try to extract complete messages
                while len(buffer) >= 21:  # Minimum wrapped message size
                    try:
                        # Unwrap message
                        msg_type, msg_data = self.obfuscator.unwrap_message(buffer)

                        # Calculate consumed bytes
                        consumed = 21 + len(msg_data) + (len(buffer) - 21 - len(msg_data))
                        buffer = buffer[consumed:]

                        # Process message
                        if self.message_callback and msg_type == 0x01:  # Real message
                            self.message_callback(peer_id, msg_data)

                        break  # Process one message at a time

                    except ValueError:
                        # Not enough data yet
                        break
                    except Exception as e:
                        # Corrupted message, skip some bytes
                        buffer = buffer[1:]
                        break

            except socket.timeout:
                continue
            except Exception as e:
                break

        # Connection closed
        with self._lock:
            if peer_id in self.peers:
                del self.peers[peer_id]

        try:
            sock.close()
        except:
            pass

        if self.connection_callback:
            self.connection_callback(peer_id, 'disconnected')

    def send_message(self, peer_id: str, message: bytes):
        """Send a message to a peer with obfuscation."""
        with self._lock:
            if peer_id not in self.peers:
                raise ValueError(f"Peer {peer_id} not connected")

            sock = self.peers[peer_id]

        # Wrap message with obfuscation
        wrapped = self.obfuscator.wrap_message(message, message_type=0x01)

        # Add timing jitter
        jitter = self.obfuscator.add_timing_jitter()
        time.sleep(jitter)

        # Send message
        try:
            sock.sendall(wrapped)
        except Exception as e:
            raise ConnectionError(f"Failed to send message to {peer_id}: {e}")

    def broadcast_message(self, message: bytes):
        """Broadcast a message to all connected peers."""
        with self._lock:
            peer_ids = list(self.peers.keys())

        for peer_id in peer_ids:
            try:
                self.send_message(peer_id, message)
            except Exception as e:
                print(f"Failed to send to {peer_id}: {e}")

    def set_message_callback(self, callback: Callable):
        """Set callback for received messages: callback(peer_id, message)"""
        self.message_callback = callback

    def set_connection_callback(self, callback: Callable):
        """Set callback for connection events: callback(peer_id, event)"""
        self.connection_callback = callback

    def get_peer_list(self) -> list:
        """Get list of connected peer IDs."""
        with self._lock:
            return list(self.peers.keys())

    def get_address(self) -> tuple:
        """Get the node's listening address."""
        return (self.host, self.port)
