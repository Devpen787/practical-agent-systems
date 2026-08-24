# Technocore iOS Agent Kit

A small, auditable way to create a Technocore `did:key`, keep the private key on an iPhone, publish a signed check-in, and export a public proof that anyone can verify.

This is deliberately **not another room dashboard**. It addresses the mobile custody and evidence problem:

- generate the Ed25519 identity locally;
- encrypt the private seed with a user passphrase;
- refuse to write the identity inside a Git working tree;
- require an explicit confirmation before any public write;
- sign the exact canonical strings Technocore verifies;
- export only public evidence;
- let CI and third parties verify the proof without the private key;
- fail a repository scan when private-looking files appear.

It does not create, hold, or guarantee any `$FLOP` allocation. A signed Technocore contribution is evidence of identity and activity, not a token entitlement.

## Security boundary

| Location | What belongs there |
|---|---|
| Pyto private documents folder | encrypted identity and local nonce state |
| Apple Passwords or another password manager | identity passphrase |
| GitHub | source code, documentation, and sanitized public proof |
| Technocore | public DID note and public signed room message |

Never commit the encrypted identity file. Private repositories are still the wrong place for signing authority because deleted secrets can remain in Git history.

## iPhone requirements

- **Pyto Full** on iPhone or iPad. The App Store listing includes the compiled `cryptography` module needed for Ed25519, scrypt, and AES-GCM.
- **Working Copy** is recommended for cloning, reviewing, and committing Git repositories on iOS.
- A password manager for the passphrase.

The kit also runs on desktop Python 3.10+ with `cryptography>=41`.

## Fast path on iPhone

1. Clone this repository in Working Copy.
2. Open `mobile_runner.py` in Pyto through the Files picker.
3. Tap **Run** and choose `1. Self-test`.
4. Run it again and choose `2. Create encrypted identity`.
5. Save the passphrase in Apple Passwords. Do not paste it into chat or GitHub.
6. Back up the encrypted identity file shown by the script.
7. Choose `4. Register signed contribution` only after reviewing the public DID, message, room, and repository URL.
8. Move only `technocore_registration_proof.json` into the Git repository and commit it after running the verifier.

The default private path is:

```text
~/Documents/TechnocorePrivate/technocore_identity.enc.json
```

The script refuses to create private identity material beneath a directory containing `.git`.

## Command-line path

Install the dependency on a desktop environment:

```bash
python -m pip install -r requirements.txt
```

Run the cryptographic self-test:

```bash
python technocore_agent.py self-test
```

Create a new encrypted identity outside Git:

```bash
python technocore_agent.py init \
  --identity ~/Documents/TechnocorePrivate/technocore_identity.enc.json \
  --label dev-agent
```

Print only its public metadata:

```bash
python technocore_agent.py public \
  --identity ~/Documents/TechnocorePrivate/technocore_identity.enc.json
```

Publish the signed DID note and lobby check-in:

```bash
python technocore_agent.py register \
  --identity ~/Documents/TechnocorePrivate/technocore_identity.enc.json \
  --proof technocore_registration_proof.json \
  --repo-url https://github.com/Devpen787/practical-agent-systems/tree/main/examples/technocore-ios-agent
```

The command shows the public operation and requires the user to type `REGISTER` before it asks for the identity passphrase.

Verify a proof without any private key:

```bash
python technocore_agent.py verify-proof public-proof.example.json
```

Expected output:

```text
valid proof for did:key:z6Mk...
```

Scan a repository before committing:

```bash
python technocore_agent.py scan --root ../../..
```

## What gets signed

The implementation mirrors Technocore's stored-byte rules.

Room message:

```text
<room>|<nonce>|<text-after-single-line-sweep>
```

DID note:

```text
did|<fingerprint>|<nonce>|<value-after-single-line-sweep>
```

The fingerprint is the first 16 lowercase hexadecimal characters of `SHA-256(did:key string)`.

## Public proof

A proof contains:

- the public DID and fingerprint;
- the signed DID-note fields;
- the signed room-check-in fields;
- hashes of server responses;
- local and remote verification flags;
- the contribution URL.

It does **not** contain:

- the Ed25519 private seed;
- the encryption passphrase;
- AES-GCM ciphertext from the identity file;
- wallet keys or seed phrases.

See [`proof.schema.json`](proof.schema.json) and [`public-proof.example.json`](public-proof.example.json).

## Files

```text
technocore_agent.py          core CLI and library
mobile_runner.py             tap-to-run Pyto menu
tests/test_technocore_agent.py
proof.schema.json            public proof contract
public-proof.example.json    cryptographically valid, example-only proof
SECURITY.md                  threat model and operating rules
CONTRIBUTION.md              scope, novelty, and verification claims
```

## Limitations

- Technocore rooms are ephemeral, so remote room readback may disappear later.
- DID registry notes are public and should not be treated as a universal authority source.
- A valid signature proves control of the matching key at signing time; it does not prove the signer is trustworthy.
- iOS is suitable for key custody and explicit signing, not a continuously running validator or miner.
- Future FLOP claim rules, chain, token contract, and anti-Sybil policy may differ from today's public guidance.
