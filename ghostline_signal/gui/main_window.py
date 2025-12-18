"""
Main window for Ghostline Signal GUI.
"""

import json
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QTextEdit, QPushButton, QListWidget, QListWidgetItem,
                               QSplitter, QLabel, QLineEdit, QDialog, QFormLayout,
                               QMessageBox, QGroupBox, QSpinBox, QDialogButtonBox,
                               QTextBrowser, QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QAction

from ..crypto import KeyManager, MessageEncryption
from ..network import P2PNode, ConnectionBroker
from ..storage import MessageStore
from ..identity import DeviceIdentity
from .widgets import MessageBubble, PeerListItem, ConnectionStatus


class MainWindow(QMainWindow):
    """Main application window."""

    message_received = Signal(str, bytes)

    def __init__(self):
        super().__init__()

        # Initialize core components
        self.identity = DeviceIdentity()
        self.key_manager = KeyManager()
        self.message_store = MessageStore()
        self.p2p_node = P2PNode()
        self.encryption = MessageEncryption()

        # Connection broker for automatic NAT traversal
        self.connection_broker = None

        # Current state
        self.current_peer_id = None
        self.sessions = {}  # peer_id -> session_key

        # Setup UI
        self.setup_ui()
        self.setup_networking()

        # Connect signals
        self.message_received.connect(self.on_message_received_signal)

        # Start P2P node
        self.start_node()

        # Initialize connection broker
        self.init_connection_broker()

        # Cleanup timer for expired sessions
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_sessions)
        self.cleanup_timer.start(60000)  # Every minute

    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(f"Ghostline Signal - {self.identity.get_device_name()}")
        self.setMinimumSize(1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left sidebar - Peers
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)
        sidebar.setMaximumWidth(250)

        # Connection status
        self.connection_status = ConnectionStatus()
        sidebar_layout.addWidget(self.connection_status)

        # Peers list
        peers_label = QLabel("Peers")
        peers_label.setFont(QFont("Arial", 12, QFont.Bold))
        sidebar_layout.addWidget(peers_label)

        self.peers_list = QListWidget()
        self.peers_list.itemClicked.connect(self.on_peer_selected)
        sidebar_layout.addWidget(self.peers_list)

        # Connect button
        connect_btn = QPushButton("Connect to Peer")
        connect_btn.clicked.connect(self.show_connect_dialog)
        sidebar_layout.addWidget(connect_btn)

        # Add peer button
        add_peer_btn = QPushButton("Add Peer Identity")
        add_peer_btn.clicked.connect(self.show_add_peer_dialog)
        sidebar_layout.addWidget(add_peer_btn)

        main_layout.addWidget(sidebar)

        # Right side - Chat
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        chat_widget.setLayout(chat_layout)

        # Chat header
        self.chat_header = QLabel("Select a peer to start messaging")
        self.chat_header.setFont(QFont("Arial", 14, QFont.Bold))
        self.chat_header.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        chat_layout.addWidget(self.chat_header)

        # Messages area
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.addStretch()
        self.messages_widget.setLayout(self.messages_layout)

        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.messages_widget)
        scroll_area.setWidgetResizable(True)
        self.scroll_area = scroll_area
        chat_layout.addWidget(scroll_area)

        # Message input
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        send_btn.setFixedWidth(80)
        input_layout.addWidget(send_btn)

        chat_layout.addLayout(input_layout)

        main_layout.addWidget(chat_widget, stretch=1)

        # Menu bar
        self.create_menu_bar()

        # Load peers
        self.load_peers()

    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        identity_action = QAction("&Device Identity", self)
        identity_action.triggered.connect(self.show_identity_dialog)
        tools_menu.addAction(identity_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def setup_networking(self):
        """Setup P2P networking callbacks."""
        self.p2p_node.set_message_callback(self.on_message_received)
        self.p2p_node.set_connection_callback(self.on_connection_event)

    def start_node(self):
        """Start the P2P node."""
        try:
            self.p2p_node.start()
            host, port = self.p2p_node.get_address()
            self.connection_status.set_listening(port)
            print(f"Node started on {host}:{port}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start node: {e}")

    def init_connection_broker(self):
        """Initialize connection broker for automatic NAT traversal."""
        try:
            device_id = self.identity.get_device_id()
            self.connection_broker = ConnectionBroker(
                self.p2p_node,
                device_id,
                use_rendezvous=False  # Disabled by default (no central server)
            )

            # Initialize in background
            def init_broker():
                self.connection_broker.set_status_callback(self.on_broker_status)
                self.connection_broker.initialize()

            import threading
            thread = threading.Thread(target=init_broker, daemon=True)
            thread.start()

        except Exception as e:
            print(f"Connection broker initialization failed: {e}")
            # Non-fatal - can still use manual connections

    def on_broker_status(self, message: str):
        """Handle connection broker status updates."""
        print(f"[Broker] {message}")
        # Could update status bar here

    def load_peers(self):
        """Load peers from storage."""
        self.peers_list.clear()
        peers = self.message_store.get_all_peers()

        for peer in peers:
            item = QListWidgetItem()
            widget = PeerListItem(
                peer['peer_id'],
                peer.get('display_name'),
                peer.get('last_seen')
            )
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, peer['peer_id'])
            self.peers_list.addItem(item)
            self.peers_list.setItemWidget(item, widget)

        # Update connection status
        peer_count = len(self.p2p_node.get_peer_list())
        if peer_count > 0:
            self.connection_status.set_connected(peer_count)

    def on_peer_selected(self, item: QListWidgetItem):
        """Handle peer selection."""
        peer_id = item.data(Qt.UserRole)
        self.current_peer_id = peer_id

        peer = self.message_store.get_peer(peer_id)
        display_name = peer.get('display_name') if peer else peer_id
        self.chat_header.setText(f"Chat with {display_name}")

        # Load messages
        self.load_messages(peer_id)

    def load_messages(self, peer_id: str):
        """Load messages for a peer."""
        # Clear existing messages
        while self.messages_layout.count() > 1:  # Keep the stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load from database
        messages = self.message_store.get_messages(peer_id)

        for msg in messages:
            try:
                # Decrypt message if we have a session key
                content = msg['content']
                session_id = msg.get('session_id')

                if session_id and session_id in self.sessions:
                    session_key = self.sessions[session_id]
                    decrypted = self.encryption.decrypt_message(content, session_key)
                    decrypted = self.encryption.remove_padding(decrypted)
                    message_text = decrypted.decode('utf-8')
                else:
                    message_text = "[Encrypted - Session key not available]"

                bubble = MessageBubble(
                    message_text,
                    msg['timestamp'],
                    msg['direction'] == 'sent'
                )
                self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)

            except Exception as e:
                print(f"Error loading message: {e}")

        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scroll messages to bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send a message to the current peer."""
        if not self.current_peer_id:
            QMessageBox.warning(self, "Warning", "Please select a peer first")
            return

        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return

        try:
            # Get or create session key
            session_id = f"session_{self.current_peer_id}_{int(datetime.now().timestamp())}"
            if self.current_peer_id not in self.sessions:
                # Generate new session key
                session_key = self.key_manager.generate_session_key()
                self.sessions[self.current_peer_id] = session_key

                # Store session
                expires_at = (datetime.now() + timedelta(hours=24)).timestamp()
                self.message_store.store_session(session_id, self.current_peer_id,
                                                session_key, expires_at)
            else:
                session_key = self.sessions[self.current_peer_id]

            # Encrypt message
            plaintext = message_text.encode('utf-8')
            padded = self.encryption.add_padding(plaintext)
            encrypted = self.encryption.encrypt_message(padded, session_key)

            # Create message envelope
            envelope = {
                'type': 'message',
                'session_id': session_id,
                'from': self.identity.get_device_id(),
                'data': encrypted.hex()
            }
            envelope_bytes = json.dumps(envelope).encode('utf-8')

            # Send to peer
            self.p2p_node.send_message(self.current_peer_id, envelope_bytes)

            # Store locally
            self.message_store.store_message(
                self.current_peer_id,
                encrypted,
                'sent',
                session_id,
                delivered=True
            )

            # Display in UI
            bubble = MessageBubble(message_text, datetime.now().timestamp(), True)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
            self.scroll_to_bottom()

            # Clear input
            self.message_input.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send message: {e}")

    def on_message_received(self, peer_id: str, message: bytes):
        """Handle received message (from P2P callback)."""
        # Emit signal to handle in main thread
        self.message_received.emit(peer_id, message)

    @Slot(str, bytes)
    def on_message_received_signal(self, peer_id: str, message: bytes):
        """Handle received message in main thread."""
        try:
            # Parse envelope
            envelope = json.loads(message.decode('utf-8'))

            if envelope.get('type') == 'message':
                session_id = envelope.get('session_id')
                encrypted_data = bytes.fromhex(envelope.get('data'))
                from_device = envelope.get('from')

                # Try to decrypt
                if peer_id in self.sessions:
                    session_key = self.sessions[peer_id]
                    try:
                        decrypted = self.encryption.decrypt_message(encrypted_data, session_key)
                        decrypted = self.encryption.remove_padding(decrypted)
                        message_text = decrypted.decode('utf-8')

                        # Store message
                        self.message_store.store_message(
                            peer_id,
                            encrypted_data,
                            'received',
                            session_id,
                            delivered=True
                        )

                        # Update last seen
                        self.message_store.update_peer_last_seen(peer_id)

                        # Display if this is the current chat
                        if peer_id == self.current_peer_id:
                            bubble = MessageBubble(message_text, datetime.now().timestamp(), False)
                            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
                            self.scroll_to_bottom()

                    except Exception as e:
                        print(f"Decryption error: {e}")

        except Exception as e:
            print(f"Error processing received message: {e}")

    def on_connection_event(self, peer_id: str, event: str):
        """Handle connection events."""
        if event == 'connected':
            print(f"Peer connected: {peer_id}")
            peer_count = len(self.p2p_node.get_peer_list())
            self.connection_status.set_connected(peer_count)
        elif event == 'disconnected':
            print(f"Peer disconnected: {peer_id}")
            peer_count = len(self.p2p_node.get_peer_list())
            if peer_count > 0:
                self.connection_status.set_connected(peer_count)
            else:
                host, port = self.p2p_node.get_address()
                self.connection_status.set_listening(port)

    def show_connect_dialog(self):
        """Show dialog to connect to a peer."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect to Peer")
        dialog.setMinimumWidth(500)

        main_layout = QVBoxLayout()

        # Tab widget for different connection methods
        tabs = QTabWidget()

        # Tab 1: Connect by Device ID (Automatic)
        device_id_tab = QWidget()
        device_id_layout = QFormLayout()

        device_id_input = QLineEdit()
        device_id_input.setPlaceholderText("e.g., 550e8400-e29b-41d4-a716-446655440000")
        device_id_layout.addRow("Device ID:", device_id_input)

        info_label = QLabel("✓ Automatic NAT traversal\n✓ No port forwarding needed\n✓ Works globally")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        device_id_layout.addRow(info_label)

        device_id_tab.setLayout(device_id_layout)
        tabs.addTab(device_id_tab, "By Device ID (Auto)")

        # Tab 2: Connect by IP/Port (Manual)
        manual_tab = QWidget()
        manual_layout = QFormLayout()

        host_input = QLineEdit()
        host_input.setPlaceholderText("e.g., 192.168.1.100 or public IP")
        manual_layout.addRow("Host:", host_input)

        port_input = QSpinBox()
        port_input.setRange(1024, 65535)
        port_input.setValue(5000)
        manual_layout.addRow("Port:", port_input)

        manual_info = QLabel("For local network or when peer has port forwarding")
        manual_info.setStyleSheet("color: #666; padding: 10px;")
        manual_layout.addRow(manual_info)

        manual_tab.setLayout(manual_layout)
        tabs.addTab(manual_tab, "By IP/Port (Manual)")

        main_layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        main_layout.addWidget(buttons)

        dialog.setLayout(main_layout)

        if dialog.exec() == QDialog.Accepted:
            current_tab = tabs.currentIndex()

            if current_tab == 0:  # Device ID
                device_id = device_id_input.text().strip()
                if device_id:
                    self.connect_by_device_id(device_id)
            else:  # Manual IP/Port
                host = host_input.text().strip()
                port = port_input.value()
                if host:
                    self.connect_by_ip_port(host, port)

    def connect_by_device_id(self, device_id: str):
        """Connect to peer using device ID (automatic NAT traversal)."""
        if not self.connection_broker:
            QMessageBox.warning(self, "Not Available",
                              "Connection broker not initialized.\nPlease use manual connection.")
            return

        # Show progress dialog
        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Discovering peer and establishing connection...",
                                  "Cancel", 0, 0, self)
        progress.setWindowTitle("Connecting")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        def attempt_connection():
            try:
                peer_id = self.connection_broker.connect_by_device_id(device_id)

                if peer_id:
                    # Add to peers if not exists
                    if not self.message_store.get_peer(peer_id):
                        self.message_store.add_peer(
                            peer_id,
                            b'',
                            display_name=device_id[:8]
                        )

                    # Update UI in main thread
                    QTimer.singleShot(0, lambda: self.on_device_id_connected(peer_id, progress))
                else:
                    QTimer.singleShot(0, lambda: self.on_device_id_failed(progress))

            except Exception as e:
                QTimer.singleShot(0, lambda: self.on_device_id_error(str(e), progress))

        import threading
        thread = threading.Thread(target=attempt_connection, daemon=True)
        thread.start()

    def on_device_id_connected(self, peer_id: str, progress):
        """Handle successful device ID connection."""
        progress.close()
        QMessageBox.information(self, "Success",
                              f"Connected to peer!\n\nPeer ID: {peer_id}")
        self.load_peers()

    def on_device_id_failed(self, progress):
        """Handle failed device ID connection."""
        progress.close()
        QMessageBox.warning(self, "Connection Failed",
                          "Could not discover or connect to peer.\n\n"
                          "Possible reasons:\n"
                          "- Peer is offline\n"
                          "- Peer not registered on rendezvous server\n"
                          "- Network issues\n\n"
                          "Try using manual IP/Port connection instead.")

    def on_device_id_error(self, error: str, progress):
        """Handle device ID connection error."""
        progress.close()
        QMessageBox.critical(self, "Error", f"Connection error: {error}")

    def connect_by_ip_port(self, host: str, port: int):
        """Connect to peer using IP and port (manual)."""
        try:
            peer_id = self.p2p_node.connect_to_peer(host, port)
            QMessageBox.information(self, "Success", f"Connected to {peer_id}")

            # Add to peers if not exists
            if not self.message_store.get_peer(peer_id):
                self.message_store.add_peer(
                    peer_id,
                    b'',  # Public key will be exchanged later
                    display_name=f"{host}:{port}"
                )

            self.load_peers()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect: {e}")

    def show_add_peer_dialog(self):
        """Show dialog to add a peer identity."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Peer Identity")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        peer_id_input = QLineEdit()
        layout.addRow("Peer ID:", peer_id_input)

        display_name_input = QLineEdit()
        layout.addRow("Display Name:", display_name_input)

        public_key_input = QTextEdit()
        public_key_input.setPlaceholderText("Paste peer's public key here...")
        public_key_input.setMaximumHeight(150)
        layout.addRow("Public Key:", public_key_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            peer_id = peer_id_input.text().strip()
            display_name = display_name_input.text().strip()
            public_key = public_key_input.toPlainText().strip().encode('utf-8')

            if peer_id and public_key:
                try:
                    self.message_store.add_peer(peer_id, public_key, display_name)
                    self.load_peers()
                    QMessageBox.information(self, "Success", "Peer added successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add peer: {e}")

    def show_identity_dialog(self):
        """Show device identity dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Device Identity")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Identity info
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout()

        device_id_label = QLabel(self.identity.get_device_id())
        device_id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("Device ID:", device_id_label)

        device_name_label = QLabel(self.identity.get_device_name())
        info_layout.addRow("Device Name:", device_name_label)

        fingerprint = self.identity.format_fingerprint(self.identity.get_device_fingerprint())
        fingerprint_label = QLabel(fingerprint)
        fingerprint_label.setFont(QFont("Courier", 12))
        fingerprint_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("Fingerprint:", fingerprint_label)

        host, port = self.p2p_node.get_address()
        address_label = QLabel(f"{host}:{port}")
        info_layout.addRow("Listening Address:", address_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Public key
        key_group = QGroupBox("Public Key (Share with peers)")
        key_layout = QVBoxLayout()

        public_key_text = QTextBrowser()
        public_key_text.setPlainText(self.key_manager.get_public_key_bytes().decode('utf-8'))
        public_key_text.setMaximumHeight(200)
        key_layout.addWidget(public_key_text)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def show_about_dialog(self):
        """Show about dialog."""
        about_text = """
<h2>Ghostline Signal</h2>
<p>Peer-to-peer communication system designed for privacy and locality.</p>

<h3>Design Principles:</h3>
<ul>
<li>No accounts, no cloud, no servers</li>
<li>End-to-end encryption with ephemeral keys</li>
<li>Traffic obfuscation for privacy</li>
<li>Device-bound identity</li>
<li>Local-first architecture</li>
</ul>

<p><b>Warning:</b> Ghostline Signal prioritises privacy and locality over convenience.
Misuse, misconfiguration, or loss of devices can result in permanent data loss.</p>
        """

        QMessageBox.about(self, "About Ghostline Signal", about_text)

    def cleanup_sessions(self):
        """Cleanup expired sessions."""
        self.message_store.cleanup_expired_sessions()

    def closeEvent(self, event):
        """Handle window close."""
        if self.connection_broker:
            self.connection_broker.shutdown()
        self.p2p_node.stop()
        event.accept()
