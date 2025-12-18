# Ghostline Signal - Usage Guide

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

Or make it executable:
```bash
chmod +x main.py
./main.py
```

## First Time Setup

When you first run Ghostline Signal, the application will:

1. Generate a unique device identity
2. Create cryptographic keys (4096-bit RSA)
3. Start listening for P2P connections
4. Initialize local message storage

All data is stored locally in `~/.ghostline_signal/`

## Connecting to Peers

### Step 1: Exchange Device Information

1. Go to **Tools → Device Identity** to view your device information
2. Share your **Listening Address** (host:port) with your peer
3. Share your **Public Key** with your peer
4. Get your peer's public key and listening address

### Step 2: Add Peer Identity

1. Click **"Add Peer Identity"** button
2. Enter:
   - **Peer ID**: A unique identifier (e.g., host:port)
   - **Display Name**: A friendly name for this peer
   - **Public Key**: Paste the peer's public key

### Step 3: Connect to Peer

1. Click **"Connect to Peer"** button
2. Enter:
   - **Host**: Peer's IP address
   - **Port**: Peer's listening port
3. Click **OK** to establish connection

## Sending Messages

1. Select a peer from the peer list
2. Type your message in the input box at the bottom
3. Click **Send** or press Enter

All messages are:
- Encrypted end-to-end with AES-256-GCM
- Padded to obscure message length
- Transmitted with traffic obfuscation
- Stored locally in encrypted form

## Security Features

### End-to-End Encryption
- All messages encrypted with ephemeral session keys
- Session keys rotated automatically
- Private keys never leave your device

### Traffic Obfuscation
- Randomized packet sizes
- Variable timing and jitter
- Indistinguishable payload structure
- No fixed message boundaries

### Local-First Architecture
- No central servers
- No cloud sync
- All data stored locally
- No metadata exposure

## Privacy Considerations

### What Ghostline Signal Does NOT Track:
- No online/offline status
- No read receipts
- No typing indicators
- No message delivery confirmations
- No user presence information

### Data Storage
All data is stored locally in:
- `~/.ghostline_signal/keys/` - Cryptographic keys
- `~/.ghostline_signal/messages.db` - Encrypted messages
- `~/.ghostline_signal/identity.json` - Device identity

### Device Fingerprint
Each device has a unique fingerprint for verification. When establishing trust with a peer, verify their fingerprint through a separate secure channel.

## Troubleshooting

### Can't Connect to Peer
- Ensure both devices are on the same network or have direct connectivity
- Check firewall settings allow connections on the listening port
- Verify the peer's address and port are correct

### Messages Not Decrypting
- Ensure you have the peer's correct public key
- Session keys are ephemeral - messages from old sessions may not decrypt
- Check that both devices have synchronized session keys

### Connection Lost
- Connections may drop due to network issues
- Ghostline Signal does not automatically reconnect
- Click "Connect to Peer" again to reestablish connection

## Advanced Usage

### Running on Custom Port
The application automatically selects an available port. To use a specific port, modify the P2PNode initialization in `ghostline_signal/gui/main_window.py`:

```python
self.p2p_node = P2PNode(port=YOUR_PORT)
```

### Remote Access
To accept connections from outside your local network:
1. Configure port forwarding on your router
2. Use your public IP address for peer connections
3. Ensure proper firewall configuration

### Multiple Devices
Each device has a unique identity. To use Ghostline Signal on multiple devices:
- Each device maintains separate keys and storage
- No automatic sync between devices (by design)
- Messages are device-specific

## Security Warnings

1. **Device Loss**: If you lose your device, you lose all messages on it. There is no recovery.

2. **Physical Security**: Physical access to your device means access to your messages. Keep your device secure.

3. **Network Observation**: While traffic is obfuscated, an observer can see data is moving between devices.

4. **Trust Establishment**: Always verify peer fingerprints through a separate secure channel before trusting their identity.

5. **No Plausible Deniability**: Encrypted data on your device can be identified as encrypted messaging data.

## Philosophy

Ghostline Signal prioritizes privacy and control over convenience:

- **No convenience features that compromise privacy**
- **No cloud services**
- **No account recovery**
- **No multi-device sync**

If these tradeoffs are acceptable, Ghostline Signal provides a secure, private communication system with no external dependencies.

## Support

Ghostline Signal is under active development. Protocols and behaviors may change.

For issues or questions, refer to the main README.md file.
