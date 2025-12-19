#!/usr/bin/env python3
"""
Ghostline Signal Rendezvous Server

A simple, privacy-preserving server for device ID-based peer discovery.
Stores temporary device_id -> connection_info mappings.

Privacy Features:
- In-memory only (no persistent storage)
- Automatic expiration (5 minutes without heartbeat)
- No message content or metadata
- Self-hostable
- Optional (P2P works without it)

Usage:
    python3 rendezvous_server.py [--port PORT] [--host HOST]

Default: http://0.0.0.0:8080
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional
import argparse


class DeviceRegistry:
    """In-memory registry of devices and their connection info."""

    def __init__(self, expiration_seconds: int = 300):
        """
        Initialize device registry.

        Args:
            expiration_seconds: Time before registration expires (default: 5 minutes)
        """
        self.devices: Dict[str, dict] = {}
        self.expiration_seconds = expiration_seconds
        self.lock = threading.Lock()

        # Connection requests for coordinated NAT traversal
        # Format: {target_device_id: [{requester_id, requester_info, timestamp}, ...]}
        self.connect_requests: Dict[str, list] = {}
        self.request_expiration = 30  # Connection requests expire after 30 seconds

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def register(self, device_id: str, public_addr: dict, local_addr: dict = None) -> bool:
        """Register or update a device."""
        with self.lock:
            self.devices[device_id] = {
                'device_id': device_id,
                'public_addr': public_addr,
                'local_addr': local_addr,
                'last_seen': time.time(),
                'registered_at': self.devices.get(device_id, {}).get('registered_at', time.time())
            }
            return True

    def lookup(self, device_id: str) -> Optional[dict]:
        """Look up a device's connection info."""
        with self.lock:
            device = self.devices.get(device_id)
            if device:
                # Check if expired
                age = time.time() - device['last_seen']
                if age > self.expiration_seconds:
                    del self.devices[device_id]
                    return None
                return {
                    'device_id': device['device_id'],
                    'public_addr': device['public_addr'],
                    'local_addr': device['local_addr']
                }
            return None

    def heartbeat(self, device_id: str) -> bool:
        """Update last_seen timestamp for a device."""
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id]['last_seen'] = time.time()
                return True
            return False

    def unregister(self, device_id: str) -> bool:
        """Unregister a device."""
        with self.lock:
            if device_id in self.devices:
                del self.devices[device_id]
                return True
            return False

    def get_stats(self) -> dict:
        """Get server statistics."""
        with self.lock:
            now = time.time()
            active_devices = sum(
                1 for d in self.devices.values()
                if (now - d['last_seen']) <= self.expiration_seconds
            )
            pending_requests = sum(len(reqs) for reqs in self.connect_requests.values())
            return {
                'total_registered': len(self.devices),
                'active_devices': active_devices,
                'pending_requests': pending_requests,
                'expiration_seconds': self.expiration_seconds,
                'uptime': int(now - getattr(self, 'start_time', now))
            }

    def add_connect_request(self, requester_id: str, target_id: str) -> Optional[dict]:
        """
        Add a connection request from requester to target.
        Returns the target's device info if found, None otherwise.
        """
        with self.lock:
            # Check if target is registered
            target_info = self.devices.get(target_id)
            if not target_info:
                return None

            # Check if expired
            if time.time() - target_info['last_seen'] > self.expiration_seconds:
                return None

            # Get requester info
            requester_info = self.devices.get(requester_id)
            if not requester_info:
                return None

            # Add request
            if target_id not in self.connect_requests:
                self.connect_requests[target_id] = []

            # Remove any existing request from this requester
            self.connect_requests[target_id] = [
                r for r in self.connect_requests[target_id]
                if r['requester_id'] != requester_id
            ]

            # Add new request
            self.connect_requests[target_id].append({
                'requester_id': requester_id,
                'requester_info': {
                    'device_id': requester_id,
                    'public_addr': requester_info['public_addr'],
                    'local_addr': requester_info['local_addr']
                },
                'timestamp': time.time()
            })

            return {
                'device_id': target_id,
                'public_addr': target_info['public_addr'],
                'local_addr': target_info['local_addr']
            }

    def get_connect_requests(self, device_id: str) -> list:
        """Get pending connection requests for a device."""
        with self.lock:
            now = time.time()
            requests = self.connect_requests.get(device_id, [])

            # Filter out expired requests
            valid_requests = [
                r for r in requests
                if now - r['timestamp'] < self.request_expiration
            ]

            # Update stored requests
            if valid_requests:
                self.connect_requests[device_id] = valid_requests
            elif device_id in self.connect_requests:
                del self.connect_requests[device_id]

            return valid_requests

    def clear_connect_request(self, target_id: str, requester_id: str) -> bool:
        """Clear a specific connection request."""
        with self.lock:
            if target_id in self.connect_requests:
                original_len = len(self.connect_requests[target_id])
                self.connect_requests[target_id] = [
                    r for r in self.connect_requests[target_id]
                    if r['requester_id'] != requester_id
                ]
                if not self.connect_requests[target_id]:
                    del self.connect_requests[target_id]
                return len(self.connect_requests.get(target_id, [])) < original_len
            return False

    def _cleanup_loop(self):
        """Periodically remove expired devices and connection requests."""
        while True:
            time.sleep(60)  # Check every minute
            with self.lock:
                now = time.time()

                # Clean up expired devices
                expired = [
                    device_id for device_id, device in self.devices.items()
                    if (now - device['last_seen']) > self.expiration_seconds
                ]
                for device_id in expired:
                    del self.devices[device_id]

                if expired:
                    print(f"[Cleanup] Removed {len(expired)} expired device(s)")

                # Clean up expired connection requests
                expired_requests = 0
                for target_id in list(self.connect_requests.keys()):
                    original_len = len(self.connect_requests[target_id])
                    self.connect_requests[target_id] = [
                        r for r in self.connect_requests[target_id]
                        if now - r['timestamp'] < self.request_expiration
                    ]
                    expired_requests += original_len - len(self.connect_requests[target_id])
                    if not self.connect_requests[target_id]:
                        del self.connect_requests[target_id]

                if expired_requests:
                    print(f"[Cleanup] Removed {expired_requests} expired connection request(s)")


class RendezvousHandler(BaseHTTPRequestHandler):
    """HTTP request handler for rendezvous server."""

    # Class variable to hold the registry
    registry: DeviceRegistry = None

    def do_GET(self):
        """Handle GET requests (stats, health check)."""
        parsed = urlparse(self.path)

        if parsed.path == '/':
            self._send_response(200, {
                'service': 'Ghostline Signal Rendezvous Server',
                'status': 'running',
                'api_endpoint': '/api',
                'stats_endpoint': '/stats'
            })

        elif parsed.path == '/stats':
            stats = self.registry.get_stats()
            self._send_response(200, stats)

        elif parsed.path == '/health':
            self._send_response(200, {'status': 'ok'})

        else:
            self._send_response(404, {'error': 'Not found'})

    def do_POST(self):
        """Handle POST requests (API calls)."""
        if self.path != '/api':
            self._send_response(404, {'error': 'Not found'})
            return

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self._send_response(400, {'error': 'Invalid JSON'})
            return

        action = request.get('action')

        if action == 'register':
            self._handle_register(request)
        elif action == 'lookup':
            self._handle_lookup(request)
        elif action == 'heartbeat':
            self._handle_heartbeat(request)
        elif action == 'unregister':
            self._handle_unregister(request)
        elif action == 'connect_request':
            self._handle_connect_request(request)
        elif action == 'get_connect_requests':
            self._handle_get_connect_requests(request)
        elif action == 'clear_connect_request':
            self._handle_clear_connect_request(request)
        else:
            self._send_response(400, {'error': 'Unknown action'})

    def _handle_register(self, request: dict):
        """Handle device registration."""
        device_id = request.get('device_id')
        public_addr = request.get('public_addr')

        if not device_id or not public_addr:
            self._send_response(400, {'error': 'Missing device_id or public_addr'})
            return

        local_addr = request.get('local_addr')

        success = self.registry.register(device_id, public_addr, local_addr)

        if success:
            print(f"[Register] Device: {device_id[:8]}... @ {public_addr.get('ip')}:{public_addr.get('port')}")
            self._send_response(200, {
                'status': 'ok',
                'message': 'Device registered',
                'device_id': device_id
            })
        else:
            self._send_response(500, {'error': 'Registration failed'})

    def _handle_lookup(self, request: dict):
        """Handle device lookup."""
        device_id = request.get('device_id')

        if not device_id:
            self._send_response(400, {'error': 'Missing device_id'})
            return

        device_info = self.registry.lookup(device_id)

        if device_info:
            print(f"[Lookup] Device: {device_id[:8]}... found")
            self._send_response(200, {
                'status': 'ok',
                'device_info': device_info
            })
        else:
            print(f"[Lookup] Device: {device_id[:8]}... not found")
            self._send_response(404, {
                'status': 'not_found',
                'error': 'Device not found or expired'
            })

    def _handle_heartbeat(self, request: dict):
        """Handle heartbeat."""
        device_id = request.get('device_id')

        if not device_id:
            self._send_response(400, {'error': 'Missing device_id'})
            return

        success = self.registry.heartbeat(device_id)

        if success:
            self._send_response(200, {'status': 'ok'})
        else:
            self._send_response(404, {'error': 'Device not registered'})

    def _handle_unregister(self, request: dict):
        """Handle device unregistration."""
        device_id = request.get('device_id')

        if not device_id:
            self._send_response(400, {'error': 'Missing device_id'})
            return

        success = self.registry.unregister(device_id)

        if success:
            print(f"[Unregister] Device: {device_id[:8]}...")
            self._send_response(200, {'status': 'ok'})
        else:
            self._send_response(404, {'error': 'Device not registered'})

    def _handle_connect_request(self, request: dict):
        """Handle connection request (for coordinated NAT traversal)."""
        requester_id = request.get('requester_id')
        target_id = request.get('target_id')

        if not requester_id or not target_id:
            self._send_response(400, {'error': 'Missing requester_id or target_id'})
            return

        target_info = self.registry.add_connect_request(requester_id, target_id)

        if target_info:
            print(f"[ConnectRequest] {requester_id[:8]}... -> {target_id[:8]}...")
            self._send_response(200, {
                'status': 'ok',
                'target_info': target_info
            })
        else:
            self._send_response(404, {
                'status': 'not_found',
                'error': 'Target device not found or requester not registered'
            })

    def _handle_get_connect_requests(self, request: dict):
        """Handle getting pending connection requests."""
        device_id = request.get('device_id')

        if not device_id:
            self._send_response(400, {'error': 'Missing device_id'})
            return

        requests = self.registry.get_connect_requests(device_id)

        if requests:
            print(f"[GetRequests] {device_id[:8]}... has {len(requests)} pending request(s)")

        self._send_response(200, {
            'status': 'ok',
            'requests': requests
        })

    def _handle_clear_connect_request(self, request: dict):
        """Handle clearing a connection request."""
        target_id = request.get('target_id')
        requester_id = request.get('requester_id')

        if not target_id or not requester_id:
            self._send_response(400, {'error': 'Missing target_id or requester_id'})
            return

        success = self.registry.clear_connect_request(target_id, requester_id)
        self._send_response(200, {'status': 'ok', 'cleared': success})

    def _send_response(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress default logging (we have custom logging)."""
        pass


def main():
    """Run the rendezvous server."""
    parser = argparse.ArgumentParser(description='Ghostline Signal Rendezvous Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--expiration', type=int, default=300,
                       help='Device expiration time in seconds (default: 300)')
    args = parser.parse_args()

    # Create registry
    registry = DeviceRegistry(expiration_seconds=args.expiration)
    registry.start_time = time.time()

    # Set registry on handler class
    RendezvousHandler.registry = registry

    # Create server
    server = HTTPServer((args.host, args.port), RendezvousHandler)

    print("=" * 60)
    print("Ghostline Signal Rendezvous Server")
    print("=" * 60)
    print(f"Listening on: http://{args.host}:{args.port}")
    print(f"API endpoint: http://{args.host}:{args.port}/api")
    print(f"Stats: http://{args.host}:{args.port}/stats")
    print(f"Device expiration: {args.expiration} seconds")
    print()
    print("Privacy Features:")
    print("  ✓ In-memory only (no persistent storage)")
    print("  ✓ Automatic expiration")
    print("  ✓ No message content stored")
    print("  ✓ Self-hostable")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
        print("Server stopped.")


if __name__ == "__main__":
    main()
