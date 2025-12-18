# Ghostline Signal - Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation Steps

### 1. Clone the Repository (if needed)

```bash
git clone <repository-url>
cd Ghostline-Signal
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install PySide6>=6.6.0 cryptography>=41.0.0
```

### 4. Run the Application

```bash
python main.py
```

Or:

```bash
chmod +x main.py
./main.py
```

## Alternative Installation (Using setup.py)

```bash
pip install -e .
ghostline-signal
```

## Troubleshooting

### Python Version Issues

Ensure you're using Python 3.8 or higher:

```bash
python --version
```

If needed, use `python3` explicitly:

```bash
python3 main.py
```

### PySide6 Installation Issues

If PySide6 fails to install, try:

```bash
pip install --upgrade pip
pip install PySide6
```

On some systems, you may need additional dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip
sudo apt-get install libxcb-xinerama0 libxcb-cursor0
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-devel
```

**macOS:**
```bash
brew install python3
```

### Cryptography Module Issues

If the cryptography module fails to install:

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install gcc libffi-devel python3-devel openssl-devel
```

**macOS:**
```bash
brew install openssl
```

### Permission Errors

If you encounter permission errors when running:

```bash
chmod +x main.py
```

### Import Errors

If you get import errors, make sure you're running from the project root directory:

```bash
cd /path/to/Ghostline-Signal
python main.py
```

## Verifying Installation

To verify the installation is correct, you can test the imports:

```bash
python3 -c "from ghostline_signal.network import P2PNode; print('Installation OK')"
```

## System Requirements

### Minimum:
- Python 3.8+
- 512 MB RAM
- 100 MB disk space

### Recommended:
- Python 3.10+
- 1 GB RAM
- 500 MB disk space (for message storage)

## Network Configuration

### Firewall Configuration

Ghostline Signal needs to accept incoming connections. Configure your firewall to allow the application:

**Linux (ufw):**
```bash
sudo ufw allow 5000:6000/tcp  # Allow port range
```

**Linux (firewalld):**
```bash
sudo firewall-cmd --add-port=5000-6000/tcp --permanent
sudo firewall-cmd --reload
```

### Router Configuration (Optional)

For connections from outside your local network:

1. Configure port forwarding on your router
2. Forward a port (e.g., 5555) to your local machine
3. Use your public IP address when sharing connection info

## Data Directory

Ghostline Signal stores all data locally in:

```
~/.ghostline_signal/
├── keys/
│   ├── device_private.key
│   └── device_public.pem
├── messages.db
└── identity.json
```

### Backup

To backup your data:

```bash
tar -czf ghostline-backup.tar.gz ~/.ghostline_signal/
```

### Restore

```bash
tar -xzf ghostline-backup.tar.gz -C ~/
```

## Security Considerations

1. **File Permissions**: The application sets secure permissions (0600) on sensitive files
2. **Private Keys**: Never share your private key file
3. **Database**: The messages.db file contains encrypted messages
4. **Network**: Use secure networks when connecting to peers

## Uninstallation

To remove Ghostline Signal:

1. Remove the application directory
2. Remove the data directory:
   ```bash
   rm -rf ~/.ghostline_signal
   ```

## Development Setup

For development:

```bash
# Install in development mode
pip install -e .

# Run tests (if available)
python -m pytest

# Format code
black ghostline_signal/

# Type checking
mypy ghostline_signal/
```

## Getting Help

- Check the README.md for project overview
- Check USAGE.md for usage instructions
- Report issues on the project repository

## Next Steps

After installation, see USAGE.md for instructions on:
- Setting up your first connection
- Exchanging keys with peers
- Sending encrypted messages
