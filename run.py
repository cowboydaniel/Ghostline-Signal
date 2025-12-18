#!/usr/bin/env python3
"""
Ghostline Signal - Quick Run Script
Installs dependencies if needed and starts the application.
"""

import subprocess
import sys
import importlib.util
from pathlib import Path


def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    dependencies = {
        'PySide6': 'PySide6>=6.6.0',
        'cryptography': 'cryptography>=41.0.0'
    }

    missing = []

    print("Checking dependencies...")
    for package, pip_name in dependencies.items():
        if importlib.util.find_spec(package) is None:
            missing.append(pip_name)
            print(f"  ✗ {package} - NOT FOUND")
        else:
            print(f"  ✓ {package} - OK")

    if missing:
        print(f"\nInstalling {len(missing)} missing package(s)...")
        for package in missing:
            print(f"  Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"  ✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ Failed to install {package}")
                print(f"    Error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
                print(f"\nPlease install manually:")
                print(f"  pip install {package}")
                return False
    else:
        print("\nAll dependencies satisfied!")

    return True


def main():
    """Main entry point."""
    print("=" * 50)
    print("Ghostline Signal - P2P Encrypted Messaging")
    print("=" * 50)
    print()

    # Change to script directory
    script_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(script_dir))

    # Check and install dependencies
    if not check_and_install_dependencies():
        print("\n⚠️  Dependency installation failed.")
        print("Please install dependencies manually and try again:")
        print("  pip install PySide6 cryptography")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Starting Ghostline Signal...")
    print("=" * 50)
    print()

    # Import and run the application
    try:
        from PySide6.QtWidgets import QApplication
        from ghostline_signal.gui import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Ghostline Signal")
        app.setOrganizationName("Ghostline")
        app.setApplicationVersion("0.1.0")

        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print("\nTrying to reinstall dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--force-reinstall',
                              'PySide6', 'cryptography'])
        print("\nPlease run the script again:")
        print(f"  python3 {__file__}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
