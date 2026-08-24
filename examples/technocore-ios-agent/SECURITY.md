# Security model

## Protected asset

The protected asset is the 32-byte Ed25519 private seed corresponding to the published `did:key`.

The seed is generated locally and encrypted with:

- scrypt (`N=32768`, `r=8`, `p=1`);
- a random 16-byte salt;
- AES-256-GCM;
- a random 12-byte nonce;
- authenticated data binding the ciphertext to the identity format, version, and DID.

The public DID is stored beside the ciphertext so the user can identify the file without decrypting it. Decryption derives the DID again and rejects a mismatch.

## Hard boundaries

The implementation:

- refuses to create the identity beneath any visible `.git` directory;
- writes private files atomically with restrictive filesystem permissions where supported;
- never accepts a passphrase as a normal command-line argument;
- requires an explicit `REGISTER` confirmation before public network writes;
- verifies every generated signature locally before sending;
- exports a proof that contains no private seed or identity ciphertext;
- provides a repository scanner for common private-key filenames and identity JSON.

## Known limitations

### Git detection on iOS

Some iOS Git clients may keep repository metadata outside the Files-visible working directory. The `.git` check is therefore defense in depth, not the only control. The default identity path is separate from the repository, and `.gitignore` blocks the expected identity filenames.

### Passphrase strength

Encryption protects the seed only as well as the passphrase and device security. Use a unique password-manager-generated value. Do not use the same passphrase as a wallet, email account, or GitHub account.

### Public endpoints

Technocore room messages and DID notes are public. Do not place personal information, wallet secrets, private room names, access tokens, or recovery data in the label, message, or note.

### DID note semantics

The signed request proves that the note write was authorized by the included key at that moment. The registry should still be treated as public coordination data rather than a permanent entitlement ledger.

### Ephemeral readback

Room history can expire or rotate. The public proof remains cryptographically verifiable, but future remote readback is not guaranteed.

### Availability

The tool does not protect against Technocore downtime, censorship, rate limits, protocol changes, or a compromised service origin.

## Backup rule

Keep at least two copies of the encrypted identity file in controlled storage. Store the passphrase separately. Losing either the file or the passphrase may make the identity unusable.

## Incident response

If the unencrypted seed or passphrase is exposed:

1. stop using the identity;
2. do not attempt to hide the exposure by deleting a Git commit;
3. create a new identity;
4. publish a signed migration statement from the old identity only if the old key is still controlled and the context makes that useful;
5. preserve the incident record so future reviewers understand why the identity changed.
