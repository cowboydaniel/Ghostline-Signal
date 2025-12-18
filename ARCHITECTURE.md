# Ghostline Signal - Architecture Overview

## Project Structure

```
Ghostline-Signal/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── setup.py                   # Installation script
├── README.md                  # Project overview
├── USAGE.md                   # User guide
├── INSTALL.md                 # Installation guide
├── ARCHITECTURE.md            # This file
└── ghostline_signal/          # Main package
    ├── __init__.py
    ├── crypto/                # Cryptography module
    │   ├── __init__.py
    │   ├── keys.py           # Key generation and management
    │   └── encryption.py     # Message encryption/decryption
    ├── network/              # Networking module
    │   ├── __init__.py
    │   ├── p2p.py           # P2P node implementation
    │   └── obfuscation.py   # Traffic obfuscation
    ├── storage/             # Storage module
    │   ├── __init__.py
    │   └── local_db.py      # SQLite local storage
    ├── identity/            # Identity module
    │   ├── __init__.py
    │   └── device.py        # Device identity management
    └── gui/                 # GUI module
        ├── __init__.py
        ├── main_window.py   # Main application window
        └── widgets.py       # Custom widgets
```

## Core Components

### 1. Cryptography Module (`ghostline_signal/crypto/`)

#### keys.py - KeyManager
- **Purpose**: Manages cryptographic keys for the local device
- **Key Features**:
  - RSA-4096 key pair generation
  - Secure key storage with file permissions (0600)
  - Ephemeral session key generation (256-bit)
  - HKDF-based key derivation
  - Public key exchange functionality
  - Session key encryption/decryption using RSA-OAEP

#### encryption.py - MessageEncryption
- **Purpose**: Handles message encryption and decryption
- **Key Features**:
  - AES-256-GCM authenticated encryption
  - Random nonce generation (96-bit)
  - PKCS7-style padding for length obfuscation
  - Authenticated encryption with associated data (AEAD)

**Security Properties**:
- Private keys never leave the device
- Session keys are ephemeral and rotated
- Authenticated encryption prevents tampering
- Forward secrecy through session key rotation

### 2. Network Module (`ghostline_signal/network/`)

#### p2p.py - P2PNode
- **Purpose**: Implements peer-to-peer networking
- **Key Features**:
  - TCP-based P2P connections
  - Multi-threaded connection handling
  - Peer discovery and management
  - Message routing to peers
  - Connection lifecycle management
  - Automatic reconnection handling

#### obfuscation.py - TrafficObfuscator
- **Purpose**: Obfuscates network traffic
- **Key Features**:
  - Randomized packet sizes (128-8192 bytes)
  - Variable timing jitter (10-500ms)
  - Cover traffic generation
  - Message boundary obfuscation
  - Decoy packet injection (30% chance)
  - Generic-looking data structures

**Traffic Analysis Resistance**:
- No fixed message boundaries
- Indistinguishable from background noise
- Random timing prevents pattern analysis
- Packet sizes don't correlate with message length

### 3. Storage Module (`ghostline_signal/storage/`)

#### local_db.py - MessageStore
- **Purpose**: Local message storage and persistence
- **Key Features**:
  - SQLite-based storage
  - Message history per peer
  - Peer identity management
  - Session key storage with expiration
  - Automatic session cleanup
  - Message delivery tracking

**Database Schema**:
- **messages**: Encrypted message storage
- **peers**: Device identities and public keys
- **sessions**: Ephemeral session keys with expiration

**Privacy Properties**:
- All data stored locally
- No cloud sync or backup
- Device loss = data loss (by design)
- Secure file permissions

### 4. Identity Module (`ghostline_signal/identity/`)

#### device.py - DeviceIdentity
- **Purpose**: Manages device-bound identity
- **Key Features**:
  - UUID-based device ID generation
  - Device fingerprint for verification
  - Human-readable device names
  - Identity persistence
  - Fingerprint formatting for display

**Identity Properties**:
- Identity bound to device, not person
- No accounts or cloud identities
- Physical possession = ownership
- Fingerprint verification for trust establishment

### 5. GUI Module (`ghostline_signal/gui/`)

#### main_window.py - MainWindow
- **Purpose**: Main application interface
- **Key Features**:
  - Peer list management
  - Message history display
  - Real-time messaging interface
  - Connection management
  - Device identity display
  - Public key sharing
  - Settings and configuration

#### widgets.py - Custom Widgets
- **MessageBubble**: Visual message display
- **PeerListItem**: Peer information display
- **ConnectionStatus**: Network status indicator

**UI Philosophy**:
- No presence indicators
- No read receipts
- No typing notifications
- No social features
- Privacy-first design

## Data Flow

### Sending a Message

1. **User Input**: User types message in GUI
2. **Session Key**: Get or create ephemeral session key
3. **Padding**: Add padding to obscure message length
4. **Encryption**: Encrypt with AES-256-GCM
5. **Envelope**: Wrap in JSON envelope with metadata
6. **Obfuscation**: Apply traffic obfuscation
7. **Transmission**: Send via P2P network with timing jitter
8. **Storage**: Store encrypted message locally

### Receiving a Message

1. **Network**: Receive data from P2P peer
2. **Unwrap**: Extract message from obfuscated format
3. **Parse**: Parse JSON envelope
4. **Decrypt**: Decrypt using session key
5. **Unpad**: Remove padding
6. **Display**: Show plaintext in GUI
7. **Storage**: Store encrypted message locally

## Security Model

### Threat Model
- **Assumes**: Networks are observable and hostile
- **Protects**: Message content and metadata
- **Does NOT protect**: Device compromise, physical access
- **Trusts**: Hardware possession, local state

### Encryption Architecture

```
Message → Padding → AES-256-GCM Encryption → Traffic Obfuscation → Network
                         ↑
                    Session Key (256-bit)
                         ↑
                   Exchanged via RSA-4096
```

### Key Hierarchy

1. **Device Keys** (RSA-4096)
   - Generated once per device
   - Never exported
   - Used to exchange session keys

2. **Session Keys** (AES-256)
   - Generated per conversation
   - Ephemeral and rotated
   - Used for message encryption
   - Expire after 24 hours

### Trust Model
- Trust anchored to hardware possession
- No trusted third parties
- Peer trust established through:
  - Direct key exchange
  - Physical verification of fingerprints
  - Pre-shared material

## Network Protocol

### Message Envelope Format

```json
{
  "type": "message",
  "session_id": "session_<peer>_<timestamp>",
  "from": "<device_id>",
  "data": "<hex_encoded_encrypted_data>"
}
```

### Wire Format (Obfuscated)

```
[random_header (16 bytes)] [type (1 byte)] [length (4 bytes)] [envelope] [random_footer (variable)]
```

### Traffic Characteristics
- No fixed packet sizes
- Variable inter-packet delay
- Random decoy packets
- No correlation between message size and packet size

## Privacy Features

### What We DON'T Leak
- Message content (encrypted)
- Message length (padded and obfuscated)
- Message timing (jittered)
- Conversation metadata (local only)
- User presence (no indicators)
- Read status (no receipts)
- Typing activity (no notifications)

### What We CAN'T Hide
- That communication is happening
- Source and destination IP addresses
- Volume of traffic over time
- Connection patterns

## Performance Considerations

### Encryption
- RSA-4096: Used only for session key exchange (infrequent)
- AES-256-GCM: Used for all messages (very fast)
- Minimal overhead (<5% for typical messages)

### Network
- TCP for reliability
- Async I/O for multiple connections
- Message queuing for smooth delivery
- Automatic buffering and flow control

### Storage
- SQLite for efficient local storage
- Indexed queries for fast message retrieval
- Automatic session cleanup
- Minimal disk I/O

## Limitations and Trade-offs

### By Design
- No cloud sync → Device loss = message loss
- No multi-device → Each device is independent
- No account recovery → No reset mechanism
- No search across devices → Privacy over convenience

### Technical
- TCP only → No UDP support
- IPv4 only → IPv6 could be added
- No NAT traversal → May need port forwarding
- No group chat → Pairwise only

### Operational
- Manual key exchange → Trust establishment required
- Manual connections → No automatic discovery
- Local storage only → No redundancy
- Network observable → Traffic visible (but obfuscated)

## Future Considerations

### Potential Enhancements
- Diffie-Hellman key exchange for perfect forward secrecy
- Post-quantum cryptography (e.g., CRYSTALS-Kyber)
- Steganographic encoding for deeper obfuscation
- Onion routing for network-level anonymity
- File transfer support
- Voice/video with encrypted streams

### Integration Points
- Ghostline Studio: Generate and audit components
- Ghostline Browser: Interact with Signal-aware resources
- External tools: API for programmatic access

## Development Guidelines

### Code Organization
- Modular design with clear separation
- Each module has single responsibility
- Minimal dependencies between modules
- Clean interfaces for extensibility

### Testing
- Unit tests for crypto functions
- Integration tests for network layer
- UI tests for main workflows
- Security audits recommended

### Contributing
- Follow existing code style
- Add tests for new features
- Document security implications
- Consider privacy impact

## References

### Cryptographic Standards
- RSA-4096: FIPS 186-4
- AES-256-GCM: NIST SP 800-38D
- HKDF: RFC 5869
- RSA-OAEP: RFC 8017

### Libraries
- PySide6: Qt for Python GUI framework
- cryptography: Python cryptography library (pyca/cryptography)
- sqlite3: SQLite database (built-in)

### Inspiration
- Signal Protocol: Modern E2E encryption
- Tor: Traffic obfuscation and anonymity
- Briar: Local-first messaging
- Scuttlebutt: Decentralized social networks
