# Quick Start Guide

## Installation

### Method 1: Simple Installation (Recommended)

```bash
cd Ghostline-Signal
./install.sh
```

### Method 2: Manual Installation

```bash
cd Ghostline-Signal
pip install -r requirements.txt
```

### Method 3: Using pip (Development Mode)

```bash
cd Ghostline-Signal
pip install -e .
```

**Note:** Do NOT run `python setup.py` directly. Use pip instead.

## Running the Application

```bash
cd Ghostline-Signal
python3 main.py
```

Or if installed with pip:

```bash
ghostline-signal
```

## First Time Setup

When you first run the application:

1. The app will automatically generate:
   - Device identity (UUID + fingerprint)
   - Cryptographic keys (RSA-4096)
   - Local storage directory (~/.ghostline_signal/)

2. The app will start listening for P2P connections

3. You can now:
   - View your device identity: **Tools → Device Identity**
   - Share your public key with peers
   - Connect to peers: **Connect to Peer** button

## Connecting with a Peer

### Step 1: Exchange Information

**On your device:**
1. Go to **Tools → Device Identity**
2. Note your **Listening Address** (e.g., 192.168.1.100:5555)
3. Copy your **Public Key**

**Share with your peer:**
- Your listening address
- Your public key

**Get from your peer:**
- Their listening address
- Their public key

### Step 2: Add Peer Identity

1. Click **"Add Peer Identity"**
2. Fill in:
   - **Peer ID**: Their address (e.g., 192.168.1.200:5555)
   - **Display Name**: A friendly name
   - **Public Key**: Paste their public key

### Step 3: Connect

1. Click **"Connect to Peer"**
2. Enter their:
   - **Host**: Their IP address
   - **Port**: Their port number
3. Click **OK**

### Step 4: Chat!

1. Select the peer from the list
2. Type your message
3. Press Send

All messages are automatically:
- ✅ Encrypted end-to-end
- ✅ Padded to obscure length
- ✅ Obfuscated in transit
- ✅ Stored locally in encrypted form

## Troubleshooting

### "No module named 'PySide6'"

```bash
pip install PySide6
```

### "No module named 'cryptography'"

```bash
pip install cryptography
```

### Can't connect to peer

- Check firewall settings
- Ensure both devices are on same network or have direct connectivity
- Verify the IP address and port are correct
- Try having the other peer connect to you instead

### "FileNotFoundError: README.md"

Make sure you're running commands from inside the Ghostline-Signal directory:

```bash
cd Ghostline-Signal
python3 main.py
```

## Network Configuration

### Linux Firewall (ufw)

```bash
sudo ufw allow 5000:6000/tcp
```

### Finding Your IP Address

**Linux:**
```bash
ip addr show | grep "inet "
```

**macOS:**
```bash
ifconfig | grep "inet "
```

**Windows:**
```cmd
ipconfig
```

## Data Location

All data is stored locally in:
```
~/.ghostline_signal/
├── keys/
│   ├── device_private.key  (Keep secure!)
│   └── device_public.pem
├── messages.db
└── identity.json
```

## Getting Help

- **Installation issues:** See INSTALL.md
- **Usage questions:** See USAGE.md
- **Technical details:** See ARCHITECTURE.md

## Security Reminder

⚠️ **Important:**
- Keep your device secure (physical access = message access)
- Verify peer fingerprints through a separate channel
- Device loss = permanent message loss (by design)
- No account recovery available

## What's Next?

After connecting with peers:
- Messages are automatically encrypted
- No setup required for encryption
- Keys rotate automatically every 24 hours
- All data stays on your device

Enjoy secure, private, peer-to-peer communication!
