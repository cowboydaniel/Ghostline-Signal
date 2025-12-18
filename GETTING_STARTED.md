# Getting Started with Ghostline Signal

## Complete Setup Guide

This guide will get you up and running with Ghostline Signal, including the optional rendezvous server for easy device ID-based connections.

## Option 1: Quick Start (Manual Connections)

**No server needed! Works immediately.**

### 1. Install and Run

```bash
cd Ghostline-Signal
python3 run.py
```

### 2. Share Your Connection Info

Check the console output:
```
Node started on 0.0.0.0:43397
[ConnectionBroker] Public address: 49.183.173.211:30187
```

Share with your peer:
```
Public: 49.183.173.211:30187 (for internet)
Local: 10.252.142.170:43397 (for same WiFi)
```

### 3. Connect

In the GUI:
1. Click "Connect to Peer"
2. Select "By IP/Port (Manual)" tab
3. Enter peer's IP and port
4. Click OK

**Done!** You're now connected and can send encrypted messages.

---

## Option 2: With Rendezvous Server (Device ID Connections)

**Easy peer discovery - just share Device IDs!**

### 1. Start the Rendezvous Server

**Terminal 1:**
```bash
cd Ghostline-Signal
python3 rendezvous_server.py
```

Output:
```
============================================================
Ghostline Signal Rendezvous Server
============================================================
Listening on: http://0.0.0.0:8080
...
```

### 2. Start Ghostline Signal

**Terminal 2:**
```bash
cd Ghostline-Signal
python3 run.py
```

It will auto-detect the rendezvous server:
```
[ConnectionBroker] Auto-detected rendezvous server at localhost:8080
```

### 3. Get Your Device ID

In the GUI:
1. Go to **Tools → Device Identity**
2. Copy your Device ID (looks like: `550e8400-e29b-41d4-a716-446655440000`)

### 4. Share Device ID

Send your Device ID to your peer (via email, chat, etc.)

### 5. Connect by Device ID

When your peer gives you their Device ID:
1. Click "Connect to Peer"
2. Select "By Device ID (Auto)" tab
3. Paste their Device ID
4. Click OK

**Magic!** Connection established automatically - no IP addresses needed!

---

## Two Ways to Connect

### Method 1: Manual IP/Port

**Pros:**
- ✓ No server needed
- ✓ Works immediately
- ✓ Maximum privacy (direct P2P)

**Cons:**
- ✗ Need to share IP addresses
- ✗ IP changes break connection

**Best for:** Point-to-point messaging, maximum privacy

### Method 2: Device ID (Auto)

**Pros:**
- ✓ Just share Device ID once
- ✓ Works across network changes
- ✓ Easy for non-technical users

**Cons:**
- ✗ Requires rendezvous server
- ✗ Server sees IP addresses

**Best for:** Groups, easier setup

---

## Multi-User Setup

### Scenario: You and 2 Friends

**Setup A: Everyone runs rendezvous server locally**
- Each person: `python3 rendezvous_server.py`
- Use manual IP/Port to connect
- Most private, more setup

**Setup B: One person runs rendezvous server**
- Alice runs: `python3 rendezvous_server.py --host 0.0.0.0`
- Alice shares her IP: `192.168.1.100:8080`
- Bob & Charlie set:
  ```bash
  export GHOSTLINE_RENDEZVOUS_SERVER="192.168.1.100:8080"
  python3 run.py
  ```
- Everyone connects by Device ID
- Easier, Alice's server sees all IPs

**Setup C: Cloud VPS (Best for groups)**
- Deploy rendezvous server to DigitalOcean/AWS
- Everyone configures: `export GHOSTLINE_RENDEZVOUS_SERVER="your-vps:8080"`
- Most convenient
- See RENDEZVOUS_SERVER.md for deployment guide

---

## Your First Message

### After Connection is Established:

1. **Select peer** from the peer list (left sidebar)
2. **Type message** in the text box at bottom
3. **Click Send** or press Enter

Your message is now:
- ✓ Encrypted with AES-256-GCM
- ✓ Padded to hide message length
- ✓ Obfuscated during transmission
- ✓ Stored locally in encrypted form

---

## Understanding the Interface

### Left Sidebar: Peers
- **Green indicator**: Connected
- **Red indicator**: Disconnected
- **Yellow indicator**: Listening (waiting for connections)

### Top Status Bar
Shows:
- Connection status
- Number of connected peers
- Listening port

### Chat Area
- **Blue bubbles**: Your messages (sent)
- **Gray bubbles**: Peer messages (received)
- **Timestamps**: When message was sent/received

### Buttons
- **Connect to Peer**: Initiate new connection
- **Add Peer Identity**: Save peer's public key

### Menu
- **Tools → Device Identity**: View your device info, Device ID, public key
- **Help → About**: Information about Ghostline Signal

---

## Key Concepts

### Device Identity
- **Device ID**: UUID unique to your device
- **Fingerprint**: Verification code for trust
- **Public Key**: Share with peers for encryption
- **Private Key**: Never leaves your device

### Sessions
- Ephemeral session keys created for each conversation
- Automatically rotated every 24 hours
- Lost when app closes (by design for security)

### Storage
Everything is stored locally in `~/.ghostline_signal/`:
```
~/.ghostline_signal/
├── keys/
│   ├── device_private.key    # Never share!
│   └── device_public.pem      # Share with peers
├── messages.db                # Encrypted messages
└── identity.json              # Your device info
```

---

## Troubleshooting

### "Could not start node"
- Port already in use
- Try closing and reopening the app
- Or change port in code

### "Failed to connect"
- Check peer is running Ghostline Signal
- Verify IP address and port are correct
- Check firewall allows connections
- Try having peer connect to you instead

### "Peer not found on rendezvous server"
- Verify rendezvous server is running
- Check peer has configured same rendezvous server
- Registrations expire after 5 minutes
- Use manual IP/Port as fallback

### "Public IP discovery failed"
- STUN servers might be blocked
- Not critical - manual connections still work
- Check internet connection

---

## Security Best Practices

### 1. Verify Peer Identity
When adding a peer, verify their fingerprint through a separate secure channel:
- Video call
- In person
- Secure messaging app

### 2. Keep Private Key Secure
Your private key file:
- Never share it
- Has file permissions set to 0600
- If lost, regenerate (will lose message history)

### 3. Understand Privacy Levels

**Full Privacy (Manual IP/Port):**
- Direct P2P, no intermediaries
- No one can see connection metadata

**Good Privacy (With Rendezvous):**
- Rendezvous server sees: Device IDs, IP addresses, connection times
- Rendezvous server CANNOT see: Messages, contacts, keys
- Use self-hosted rendezvous for maximum control

### 4. Network Security
- Use trusted networks when possible
- Public WiFi can observe traffic (but can't decrypt)
- VPN adds another layer of privacy

---

## Next Steps

### Learn More
- **USAGE.md**: Detailed usage guide
- **ARCHITECTURE.md**: Technical deep-dive
- **NAT_TRAVERSAL.md**: How auto-connection works
- **RENDEZVOUS_SERVER.md**: Server deployment guide

### Advanced Features
- Self-host rendezvous server on VPS
- Configure HTTPS for rendezvous connections
- Set custom STUN servers
- Deploy with systemd for auto-start

### Get Help
- Check documentation first
- Review troubleshooting sections
- Report issues on GitHub

---

## Quick Reference

### Start Ghostline Signal
```bash
python3 run.py
```

### Start Rendezvous Server
```bash
python3 rendezvous_server.py
```

### With Custom Rendezvous Server
```bash
export GHOSTLINE_RENDEZVOUS_SERVER="192.168.1.100:8080"
python3 run.py
```

### View Device Identity
GUI: **Tools → Device Identity**

### Connect Methods
- **Device ID**: Automatic NAT traversal
- **IP:Port**: Manual direct connection

---

## Example Session

**Alice:**
```bash
# Start rendezvous server
python3 rendezvous_server.py

# In another terminal
python3 run.py
# Tools → Device Identity → Copy Device ID
# Send to Bob: "550e8400-e29b-41d4-a716-446655440000"
```

**Bob:**
```bash
export GHOSTLINE_RENDEZVOUS_SERVER="alice-ip:8080"
python3 run.py
# Connect to Peer → By Device ID
# Paste Alice's Device ID → Connect
# Start chatting!
```

**Messages are now:**
- ✓ End-to-end encrypted
- ✓ Traffic obfuscated
- ✓ Stored locally only
- ✓ Private and secure

---

## Summary

Ghostline Signal gives you two paths:

1. **Simple & Private**: Manual IP/Port connections, no server
2. **Easy & Convenient**: Device ID connections with optional rendezvous server

Both provide:
- End-to-end encryption
- Traffic obfuscation
- Local-only storage
- No accounts or cloud services

Choose based on your needs!

**Welcome to private, peer-to-peer messaging!** 🔒
