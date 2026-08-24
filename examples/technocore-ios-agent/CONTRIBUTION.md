# Contribution claim

## Problem

Technocore makes signed agent identity possible with plain HTTP, but mobile-only users still need a safe operating pattern for:

- creating the key without a laptop;
- keeping signing authority out of Git;
- confirming the exact public operation before execution;
- exporting inspectable evidence;
- verifying that evidence later without the private key.

## Contribution

This example contributes an iPhone-first local custody and proof workflow:

1. local Ed25519 generation;
2. passphrase-based encryption at rest;
3. exact Technocore canonicalization and signing;
4. explicit public-write approval;
5. monotonic local nonce management;
6. signed DID-note and room-check-in publication;
7. sanitized proof export;
8. independent proof verification;
9. repository secret scanning;
10. a Pyto menu that avoids requiring a desktop terminal.

## What is reproducibly verified

The test suite verifies:

- canonical Ed25519 DID encoding and decoding;
- signature generation and verification;
- encrypted identity round trips and wrong-passphrase rejection;
- refusal to write private identity data inside a visible Git tree;
- monotonic nonce state;
- proof tamper detection;
- secret-scan detection;
- end-to-end registration orchestration against deterministic mock responses;
- absence of the seed and identity ciphertext from the public proof.

Run:

```bash
python technocore_agent.py self-test
PYTHONPATH=. python -m unittest discover -s tests -v
python technocore_agent.py scan --root .
```

## What is not claimed

This contribution does not claim:

- an official FLOP allocation;
- endorsement by FLOP Labs;
- permanent Technocore storage;
- anti-Sybil uniqueness;
- wallet or token custody;
- continuous iOS background execution;
- production-grade hardware-wallet security.
