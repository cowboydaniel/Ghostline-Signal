# Ghostline Signal - Quick Start

## The Easy Way

Just run this one file:

```bash
python3 run.py
```

That's it! The script will:
1. ✓ Check for required dependencies (PySide6, cryptography)
2. ✓ Install any missing dependencies automatically
3. ✓ Start the Ghostline Signal application

## Requirements

- Python 3.8 or higher
- Internet connection (for first-time dependency installation)

## Usage

```bash
# Make executable (optional)
chmod +x run.py

# Run
./run.py

# Or
python3 run.py
```

## What Happens on First Run

1. The script checks if PySide6 and cryptography are installed
2. If missing, they're automatically installed via pip
3. The application starts
4. A device identity is created (~/.ghostline_signal/)
5. Cryptographic keys are generated
6. The GUI opens and you're ready to connect with peers!

## Troubleshooting

### "Permission denied"

```bash
chmod +x run.py
```

### "pip install failed"

Make sure you have pip installed:

```bash
# Ubuntu/Debian
sudo apt-get install python3-pip

# macOS
python3 -m ensurepip

# Then try again
python3 run.py
```

### "Python version too old"

Ghostline Signal requires Python 3.8+:

```bash
python3 --version
```

If you need to upgrade, check your system's package manager or visit python.org.

## For More Information

- **USAGE.md** - How to use the application
- **INSTALL.md** - Detailed installation instructions
- **ARCHITECTURE.md** - Technical details

## Connect with a Peer

After the app starts:

1. Go to **Tools → Device Identity** to see your listening address and public key
2. Share this info with your peer
3. Get their info
4. Click **"Add Peer Identity"** and enter their details
5. Click **"Connect to Peer"** with their address
6. Start chatting! (All messages are automatically encrypted)

Enjoy secure, private communication!
