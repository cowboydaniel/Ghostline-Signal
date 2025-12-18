# NAT Traversal and Global Connectivity

## Overview

Ghostline Signal now supports **automatic NAT traversal**, enabling global peer-to-peer connections without port forwarding or manual IP configuration.

## Features

### ✓ Connect by Device ID
- No need to know peer's IP address
- No port forwarding required
- Works across different networks worldwide
- Automatic peer discovery

### ✓ STUN-based Public IP Discovery
- Automatically discovers your public IP and port
- Uses public STUN servers (Google STUN)
- Determines NAT type and connectivity

### ✓ Smart Connection Strategy
- Tries local network first (fastest)
- Falls back to public IP if needed
- Attempts hole punching for difficult NATs
- Manual IP/Port option always available

## How It Works

### Architecture

```
Device A                    STUN Server                Device B
   |                            |                          |
   |-- Discover Public IP ----->|                          |
   |<---- Public IP:Port -------|                          |
   |                                                        |
   |                       (Optional)                       |
   |                   Rendezvous Server                    |
   |                            |                           |
   |-- Register Device ID ----->|<---- Register Device  ----|
   |                            |                           |
   |-- Lookup Peer Device ----->|                           |
   |<---- Peer Connection Info -|                           |
   |                                                         |
   |========== Direct P2P Connection =======================>|
```

### STUN (Session Traversal Utilities for NAT)

STUN helps discover:
1. Your public IP address
2. Your public port
3. Whether direct P2P is possible

Ghostline Signal uses public STUN servers:
- `stun.l.google.com:19302`
- `stun1-4.l.google.com:19302`

### Connection Broker

The Connection Broker handles:
- NAT type detection
- Public IP discovery
- Connection strategy selection
- Automatic fallback mechanisms

## Usage

### Connecting by Device ID

1. **Share Your Device ID:**
   - Open **Tools → Device Identity**
   - Copy your Device ID (UUID format)
   - Share with your peer (via secure channel)

2. **Connect to Peer:**
   - Click **"Connect to Peer"**
   - Select **"By Device ID (Auto)"** tab
   - Paste peer's Device ID
   - Click **OK**

3. **Automatic Process:**
   ```
   ✓ Discovering peer location...
   ✓ Attempting connection strategies...
   ✓ Establishing encrypted tunnel...
   ✓ Connected!
   ```

### Manual IP/Port (Fallback)

If device ID connection fails, use manual mode:

1. Get peer's IP address and port
2. Click **"Connect to Peer"**
3. Select **"By IP/Port (Manual)"** tab
4. Enter host and port
5. Click **OK**

## Connection Strategies

### Strategy 1: Local Network
If both peers are on the same network:
```
10.0.0.1:5000 <---> 10.0.0.2:5000
```
- Fastest (LAN speed)
- No NAT issues
- Works immediately

### Strategy 2: Direct Public
If at least one peer has no NAT or port forwarding:
```
203.0.113.1:5000 <---> 198.51.100.1:5000
```
- Fast (internet speed)
- Reliable
- Works with symmetric/full cone NAT

### Strategy 3: Hole Punching
For both peers behind NAT:
```
Peer A (NAT) <--- Coordinated Connection ---> Peer B (NAT)
```
- Requires simultaneous connection
- Works with most NAT types
- May need multiple attempts

## Privacy Considerations

### What's Shared
- Device ID (UUID - no personal info)
- Public IP address and port (network layer)
- Connection timing (when you're online)

### What's NOT Shared
- Message content (encrypted end-to-end)
- Message metadata (local only)
- Contact list (local only)
- Any personal information

### Rendezvous Server
Currently **DISABLED by default**. When enabled:
- Stores device_id → connection_info mapping (temporary)
- No message content or metadata
- No persistent storage
- Privacy-preserving design

## Network Requirements

### Firewall
Your firewall must allow:
- **Outbound:** All connections (usually default)
- **Inbound:** Port range for P2P (auto-selected)

Most residential firewalls work automatically.

### NAT Types
Ghostline Signal works with:
- ✓ **Full Cone NAT** - Best compatibility
- ✓ **Restricted Cone NAT** - Good compatibility
- ✓ **Port Restricted Cone NAT** - Good compatibility
- ⚠️ **Symmetric NAT** - Limited (may need relay)

### Network Restrictions
May not work with:
- ✗ Corporate firewalls blocking P2P
- ✗ Networks requiring proxy authentication
- ✗ Carrier-grade NAT (CGN) with strict filtering
- ✗ VPNs that block P2P connections

## Troubleshooting

### "Could not discover public IP"

**Problem:** STUN request failed

**Solutions:**
1. Check internet connection
2. Verify firewall allows UDP to port 19302
3. Try different network
4. Use manual IP/Port mode

### "Could not discover or connect to peer"

**Problem:** Peer lookup or connection failed

**Possible causes:**
- Peer is offline
- Peer has very restrictive NAT
- Network filtering P2P
- Both peers behind symmetric NAT

**Solutions:**
1. Verify peer is online and running Ghostline Signal
2. Try manual IP/Port connection instead
3. Check both peers can reach internet
4. One peer can enable port forwarding

### "Connection broker not initialized"

**Problem:** NAT traversal system didn't start

**Solutions:**
1. Restart application
2. Check logs for errors
3. Use manual IP/Port mode
4. File bug report if persists

## Advanced Configuration

### Custom STUN Server

Edit `nat_traversal.py` to use custom STUN server:

```python
STUN_SERVERS = [
    ('your-stun-server.com', 19302),
]
```

### Enable Rendezvous Server

To enable rendezvous server for device ID discovery:

1. Set up your own rendezvous server (see SERVER.md)
2. Update `main_window.py`:
   ```python
   self.connection_broker = ConnectionBroker(
       self.p2p_node,
       device_id,
       use_rendezvous=True,  # Enable
       rendezvous_server='your-server.com:8080'
   )
   ```

### Port Forwarding (Manual)

For best reliability, forward your port:

1. Find your port: Check **Device Identity** dialog
2. Log into your router
3. Forward TCP port to your local IP
4. Share your public IP with peers

## Security Notes

### STUN Security
- STUN requests are unauthenticated
- Reveals your public IP (already visible to network)
- Uses trusted public servers
- No sensitive data transmitted

### Rendezvous Security
- Connection info only (no messages)
- Temporary registration (expires)
- Optional (can work without it)
- Self-hostable for privacy

### Hole Punching Security
- Does not weaken encryption
- No relay servers needed
- Direct peer-to-peer only
- Full E2E encryption maintained

## Implementation Details

### Files
- `nat_traversal.py` - STUN client, rendezvous client
- `connection_broker.py` - Connection strategy and coordination
- `main_window.py` - GUI integration

### Dependencies
- No additional dependencies (uses stdlib)
- Pure Python implementation
- RFC 5389 compliant STUN

### Performance
- STUN discovery: < 1 second
- Connection establishment: 2-10 seconds
- Minimal overhead
- No impact on message throughput

## Future Enhancements

Planned features:
- ICE (Interactive Connectivity Establishment)
- TURN relay server support (for symmetric NAT)
- DHT-based peer discovery (fully decentralized)
- IPv6 support
- UPnP/NAT-PMP automatic port mapping

## References

- RFC 5389: STUN Protocol
- RFC 5766: TURN Protocol
- RFC 8445: ICE Protocol
- NAT Traversal Techniques: https://en.wikipedia.org/wiki/NAT_traversal

## Support

For issues with NAT traversal:
1. Check this guide first
2. Try manual connection
3. Review network requirements
4. Report persistent issues on GitHub
