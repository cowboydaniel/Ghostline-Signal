#!/usr/bin/env python3
"""
Ghostline Signal - Main entry point.

A peer-to-peer communication system designed for privacy and locality.
"""

import sys
from PySide6.QtWidgets import QApplication
from ghostline_signal.gui import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Ghostline Signal")
    app.setOrganizationName("Ghostline")
    app.setApplicationVersion("0.1.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
