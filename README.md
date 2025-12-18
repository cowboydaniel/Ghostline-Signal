# Ghostline Signal

Ghostline Signal is a peer to peer communication system designed for environments where privacy, locality, and control matter more than convenience or centralisation. It is part of the Ghostline Continuum and is built to function as infrastructure rather than a social product.

The core goal of Ghostline Signal is simple in principle and strict in execution: messages are only intelligible on the physical devices that create or receive them, and network traffic does not resemble conventional messaging.

## Design Philosophy

Ghostline Signal treats communication as a system level concern, not an app feature.

There are no accounts, no cloud identities, no message servers, and no readable intermediaries. Trust is anchored to hardware possession and local state, not third parties or remote services.

Signal assumes a hostile network environment and an untrusted transport layer.

## Threat Model

Ghostline Signal is designed with the following assumptions:

- Networks are observable
- Traffic may be logged, replayed, or manipulated
- Endpoints may be targeted, but not simultaneously compromised
- No external service should be trusted with message content or metadata

Ghostline Signal does not attempt to protect a user whose device is already compromised. Physical access to an endpoint is considered equivalent to ownership of that endpoint.

## Encryption Model

All message content is encrypted end to end using keys that never leave the originating or receiving device.

Key material is generated and stored locally. Private keys are non exportable by design. Session keys are ephemeral and rotated frequently.

There is no concept of server side decryption, message escrow, or recovery. If a device is lost, the messages associated with it are lost with it.

## Traffic Obfuscation

Ghostline Signal does not emit traffic that resembles chat or messaging protocols.

Instead, communication is encapsulated inside generic looking data flows designed to blend into normal background noise such as:

- Randomised packet sizes
- Variable timing and jitter
- Indistinguishable payload structure
- No fixed message boundaries

An observer can see that data is moving, but cannot reliably classify it as messaging, determine directionality, or infer content.

## Local First Architecture

All message state lives locally on participating devices.

There is no central message store.
There is no global contact list.
There is no remote history.

Devices establish trust through direct exchange, physical verification, or pre shared material. How that trust is established is explicit and user controlled.

## Identity and Presence

Identity in Ghostline Signal is bound to devices, not people.

Presence is implicit rather than broadcast. There are no online indicators, read receipts, typing notifications, or activity beacons.

Silence is a valid state and leaks no information.

## Interfaces and Deployment

Ghostline Signal is provided in two forms:

- A native desktop application built with PySide6, intended for direct use as part of the Ghostline Continuum.
- A local web interface that can be hosted directly on a user’s own device.

The web interface is designed to run entirely locally. If one user hosts Ghostline Signal on their own device and another user hosts their own instance on a separate device, the two instances can communicate directly with each other without relying on any external servers.

In both cases, the same core guarantees apply: encryption keys remain local, message content is never exposed to intermediaries, and communication occurs directly between participating devices.

## Integration with the Ghostline Continuum

Ghostline Signal is designed to operate alongside Ghostline Studio and Ghostline Browser as part of a cohesive environment.

- Studio can generate, inspect, or audit local Signal components
- Browser can interact with Signal aware resources without exposing content
- Signal can operate independently without either present

Each component remains functional on its own, but gains coherence when used together.

## Non Goals

Ghostline Signal intentionally does not provide:

- Cloud sync
- Multi device mirroring
- Account recovery
- Message search across devices
- Social discovery features

These are not missing features. They are excluded by design.

## Status

Ghostline Signal is under active development. Protocols, storage formats, and behaviours may change as the system is hardened and tested against real world constraints.

Documentation will evolve alongside the system.

## Warning

Ghostline Signal prioritises privacy and locality over convenience. Misuse, misconfiguration, or loss of devices can result in permanent data loss.

Use it only if you understand and accept those tradeoffs.
