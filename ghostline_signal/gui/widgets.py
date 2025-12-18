"""
Custom widgets for Ghostline Signal GUI.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from datetime import datetime


class MessageBubble(QFrame):
    """Custom message bubble widget."""

    def __init__(self, message: str, timestamp: float, is_sent: bool, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Message text
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Timestamp
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #888; font-size: 10px;")

        layout.addWidget(message_label)
        layout.addWidget(time_label, alignment=Qt.AlignRight)

        self.setLayout(layout)

        # Style based on sent/received
        if is_sent:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #0084ff;
                    color: white;
                    border-radius: 12px;
                    margin-left: 50px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #e4e6eb;
                    color: black;
                    border-radius: 12px;
                    margin-right: 50px;
                }
            """)


class PeerListItem(QWidget):
    """Custom peer list item widget."""

    def __init__(self, peer_id: str, display_name: str = None, last_seen: float = None,
                 parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Display name or peer ID
        name = display_name if display_name else peer_id
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)

        # Peer ID (if different from display name)
        if display_name:
            id_label = QLabel(peer_id)
            id_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(id_label)

        # Last seen
        if last_seen:
            dt = datetime.fromtimestamp(last_seen)
            last_seen_str = dt.strftime("%Y-%m-%d %H:%M")
            last_seen_label = QLabel(f"Last seen: {last_seen_str}")
            last_seen_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(last_seen_label)

        layout.addWidget(name_label)
        self.setLayout(layout)


class ConnectionStatus(QWidget):
    """Connection status indicator widget."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.status_indicator = QLabel("●")
        self.status_label = QLabel("Disconnected")

        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.setLayout(layout)
        self.set_disconnected()

    def set_connected(self, peer_count: int = 0):
        """Set status to connected."""
        self.status_indicator.setStyleSheet("color: #00ff00; font-size: 16px;")
        if peer_count > 0:
            self.status_label.setText(f"Connected ({peer_count} peer{'s' if peer_count != 1 else ''})")
        else:
            self.status_label.setText("Listening")

    def set_disconnected(self):
        """Set status to disconnected."""
        self.status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
        self.status_label.setText("Disconnected")

    def set_listening(self, port: int):
        """Set status to listening."""
        self.status_indicator.setStyleSheet("color: #ffaa00; font-size: 16px;")
        self.status_label.setText(f"Listening on port {port}")
