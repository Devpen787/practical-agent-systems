#!/usr/bin/env python3
"""Secure, iPhone-first Technocore identity and public proof tooling.

The private Ed25519 seed is generated locally, encrypted at rest, and never
included in the public proof. Network writes are explicit and human-approved.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

IDENTITY_FORMAT = "technocore-ios-agent-identity"
IDENTITY_VERSION = 1
PROOF_FORMAT = "technocore-contribution-proof"
PROOF_VERSION = 1
DEFAULT_BASE_URL = "https://technocore.chat"
DEFAULT_REPO_URL = (
    "https://github.com/Devpen787/practical-agent-systems/"
    "tree/main/examples/technocore-ios-agent"
)
DEFAULT_ROOM = "lobby"
MAX_MESSAGE_CHARS = 4096
MAX_NOTE_CHARS = 8192
MIN_PASSPHRASE_CHARS = 14
MULTICODEC_ED25519 = b"\xed\x01"
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_INDEX = {character: index for index, character in enumerate(B58_ALPHABET)}
INVISIBLE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Zl", "Zp"})
KDF_N = 2**15
KDF_R = 8
KDF_P = 1
KDF_LENGTH = 32
USER_AGENT = "technocore-ios-agent/1.0"
ROOM_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")

JsonObject = dict[str, Any]
HttpGet = Callable[[str, str, float], tuple[int, str]]


class ToolError(RuntimeError):
    """Actionable user-facing failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ToolError("invalid base64url value") from exc


def base58_encode(raw: bytes) -> str:
    if not raw:
        return ""
    leading_zeroes = len(raw) - len(raw.lstrip(b"\x00"))
    number = int.from_bytes(raw, "big")
    encoded = ""
    while number:
        number, remainder = divmod(number, 58)
        encoded = B58_ALPHABET[remainder] + encoded
    return ("1" * leading_zeroes) + encoded


def base58_decode(value: str) -> bytes:
    if not value:
        return b""
    number = 0
    for character in value:
        try:
            digit = B58_INDEX[character]
        except KeyError as exc:
            raise ToolError(f"invalid base58 character: {character!r}") from exc
        number = number * 58 + digit
    payload = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_zeroes = len(value) - len(value.lstrip("1"))
    return (b"\x00" * leading_zeroes) + payload


def clean_text(text: str, limit: int) -> str:
    cleaned = "".join(
        " " if unicodedata.category(character) in INVISIBLE_CATEGORIES else character
        for character in text
    ).strip()
    if not cleaned:
        raise ToolError("nothing visible remains after Technocore's single-line sweep")
    if len(cleaned) > limit:
        raise ToolError(f"cleaned text is {len(cleaned)} characters; limit is {limit}")
    return cleaned


def public_bytes_from_private_seed(seed: bytes) -> bytes:
    if len(seed) != 32:
        raise ToolError("Ed25519 private seed must be exactly 32 bytes")
    return (
        Ed25519PrivateKey.from_private_bytes(seed)
        .public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )


def did_from_public_bytes(public_key: bytes) -> str:
    if len(public_key) != 32:
        raise ToolError("Ed25519 public key must be exactly 32 bytes")
    return "did:key:z" + base58_encode(MULTICODEC_ED25519 + public_key)


def did_from_private_seed(seed: bytes) -> str:
    return did_from_public_bytes(public_bytes_from_private_seed(seed))


def public_bytes_from_did(did: str) -> bytes:
    prefix = "did:key:z"
    if not did.startswith(prefix):
        raise ToolError("DID must start with did:key:z")
    decoded = base58_decode(did[len(prefix) :])
    if len(decoded) != 34 or decoded[:2] != MULTICODEC_ED25519:
        raise ToolError("DID is not the canonical Ed25519 did:key form")
    return decoded[2:]


def did_fingerprint(did: str) -> str:
    public_bytes_from_did(did)
    return hashlib.sha256(did.encode("utf-8")).hexdigest()[:16]


def canonical_room(room: str, nonce: int | str, text: str) -> str:
    return f"{room}|{nonce}|{clean_text(text, MAX_MESSAGE_CHARS)}"


def canonical_note(namespace: str, key: str, nonce: int | str, value: str) -> str:
    return f"{namespace}|{key}|{nonce}|{clean_text(value, MAX_NOTE_CHARS)}"


def sign_canonical(seed: bytes, canonical: str) -> str:
    signature = Ed25519PrivateKey.from_private_bytes(seed).sign(canonical.encode("utf-8"))
    return b64url_encode(signature)


def verify_canonical(did: str, canonical: str, signature: str) -> None:
    public_key = Ed25519PublicKey.from_public_bytes(public_bytes_from_did(did))
    try:
        public_key.verify(b64url_decode(signature), canonical.encode("utf-8"))
    except InvalidSignature as exc:
        raise ToolError("signature verification failed") from exc


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _derive_encryption_key(passphrase: str, salt: bytes, *, n: int, r: int, p: int) -> bytes:
    if len(passphrase) < MIN_PASSPHRASE_CHARS:
        raise ToolError(
            f"passphrase must contain at least {MIN_PASSPHRASE_CHARS} characters"
        )
    return Scrypt(salt=salt, length=KDF_LENGTH, n=n, r=r, p=p).derive(
        passphrase.encode("utf-8")
    )


def encrypt_identity(seed: bytes, passphrase: str, *, label: str = "") -> JsonObject:
    did = did_from_private_seed(seed)
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = _derive_encryption_key(passphrase, salt, n=KDF_N, r=KDF_R, p=KDF_P)
    aad = f"{IDENTITY_FORMAT}:{IDENTITY_VERSION}:{did}".encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, seed, aad)
    return {
        "format": IDENTITY_FORMAT,
        "version": IDENTITY_VERSION,
        "created_at": utc_now(),
        "label": clean_text(label, 120) if label.strip() else "",
        "did": did,
        "fingerprint": did_fingerprint(did),
        "kdf": {
            "name": "scrypt",
            "salt": b64url_encode(salt),
            "n": KDF_N,
            "r": KDF_R,
            "p": KDF_P,
            "length": KDF_LENGTH,
        },
        "cipher": {
            "name": "aes-256-gcm",
            "nonce": b64url_encode(nonce),
            "ciphertext": b64url_encode(ciphertext),
        },
    }


def decrypt_identity(identity: JsonObject, passphrase: str) -> bytes:
    if identity.get("format") != IDENTITY_FORMAT or identity.get("version") != IDENTITY_VERSION:
        raise ToolError("unsupported identity file")
    did = str(identity.get("did", ""))
    public_bytes_from_did(did)
    kdf = identity.get("kdf")
    cipher = identity.get("cipher")
    if not isinstance(kdf, dict) or not isinstance(cipher, dict):
        raise ToolError("identity file is missing encryption metadata")
    if kdf.get("name") != "scrypt" or cipher.get("name") != "aes-256-gcm":
        raise ToolError("identity file uses unsupported encryption")
    try:
        kdf_parameters = (
            int(kdf.get("n", 0)),
            int(kdf.get("r", 0)),
            int(kdf.get("p", 0)),
            int(kdf.get("length", 0)),
        )
    except (TypeError, ValueError) as exc:
        raise ToolError("identity file has malformed scrypt parameters") from exc
    if kdf_parameters != (KDF_N, KDF_R, KDF_P, KDF_LENGTH):
        raise ToolError("identity file uses unsupported scrypt parameters")
    if identity.get("fingerprint") != did_fingerprint(did):
        raise ToolError("identity fingerprint does not match its DID")
    salt = b64url_decode(str(kdf.get("salt", "")))
    nonce = b64url_decode(str(cipher.get("nonce", "")))
    ciphertext = b64url_decode(str(cipher.get("ciphertext", "")))
    if len(salt) != 16 or len(nonce) != 12 or len(ciphertext) != 48:
        raise ToolError("identity file has malformed encryption payload lengths")
    key = _derive_encryption_key(
        passphrase,
        salt,
        n=KDF_N,
        r=KDF_R,
        p=KDF_P,
    )
    aad = f"{IDENTITY_FORMAT}:{IDENTITY_VERSION}:{did}".encode("utf-8")
    try:
        seed = AESGCM(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise ToolError("wrong passphrase or modified identity file") from exc
    if len(seed) != 32 or did_from_private_seed(seed) != did:
        raise ToolError("identity integrity check failed")
    return seed


def load_json(path: Path) -> JsonObject:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolError(f"file does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ToolError(f"expected a JSON object in {path}")
    return data


def _path_is_inside_git(path: Path) -> bool:
    current = path.expanduser().resolve()
    if current.suffix:
        current = current.parent
    while True:
        if (current / ".git").exists():
            return True
        if current.parent == current:
            return False
        current = current.parent


def atomic_write_json(
    path: Path,
    data: JsonObject,
    *,
    mode: int = 0o600,
    forbid_git: bool = False,
) -> None:
    path = path.expanduser().resolve()
    if forbid_git and _path_is_inside_git(path):
        raise ToolError(
            f"refusing to write private identity material inside a Git working tree: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def default_private_dir() -> Path:
    home = Path.home()
    documents = home / "Documents"
    root = documents if documents.exists() else home
    return root / "TechnocorePrivate"


def default_identity_path() -> Path:
    return default_private_dir() / "technocore_identity.enc.json"


def state_path_for(identity_path: Path) -> Path:
    return identity_path.expanduser().resolve().with_name("technocore_local_state.json")


def next_nonce(identity_path: Path, resource: str) -> int:
    path = state_path_for(identity_path)
    state: JsonObject = {"format": "technocore-local-state", "version": 1, "nonces": {}}
    if path.exists():
        state = load_json(path)
    nonces = state.setdefault("nonces", {})
    if not isinstance(nonces, dict):
        raise ToolError("local nonce state is malformed")
    now = time.time_ns()
    previous = int(nonces.get(resource, 0))
    nonce = max(now, previous + 1)
    if len(str(nonce)) > 19:
        raise ToolError("generated nonce exceeds Technocore's 19-digit limit")
    nonces[resource] = nonce
    state["updated_at"] = utc_now()
    atomic_write_json(path, state, mode=0o600, forbid_git=True)
    return nonce


def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.params or parsed.query or parsed.fragment:
        raise ToolError("base URL must be a plain HTTPS origin")
    if parsed.username or parsed.password:
        raise ToolError("base URL must not contain credentials")
    if parsed.path not in ("", "/"):
        raise ToolError("base URL must not contain a path")
    return base_url.rstrip("/")


def default_http_get(base_url: str, path: str, timeout: float) -> tuple[int, str]:
    base_url = _validate_base_url(base_url)
    request = Request(
        base_url + path,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is validated HTTPS
            return int(response.status), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ToolError(f"Technocore returned HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise ToolError(f"could not reach Technocore: {exc.reason}") from exc


def build_registration_payload(
    *,
    seed: bytes,
    repo_url: str,
    room: str,
    message: str,
    note_nonce: int,
    room_nonce: int,
) -> JsonObject:
    did = did_from_private_seed(seed)
    fingerprint = did_fingerprint(did)
    room = clean_text(room, 48)
    if not ROOM_RE.fullmatch(room):
        raise ToolError(
            "room name must be 1-48 lowercase letters, digits, underscores, or hyphens "
            "and start with a letter or digit"
        )
    repo_url = clean_text(repo_url, 500)
    note_value = clean_text(f"{did} platform:ios repo:{repo_url}", MAX_NOTE_CHARS)
    message = clean_text(message, MAX_MESSAGE_CHARS)

    note_canonical = canonical_note("did", fingerprint, note_nonce, note_value)
    room_canonical = canonical_room(room, room_nonce, message)
    note_signature = sign_canonical(seed, note_canonical)
    room_signature = sign_canonical(seed, room_canonical)
    verify_canonical(did, note_canonical, note_signature)
    verify_canonical(did, room_canonical, room_signature)

    note_path = (
        f"/kv/did/{quote(fingerprint, safe='')}/set-signed/"
        f"{quote(did, safe='')}/{quote(note_signature, safe='')}/{note_nonce}/"
        f"{quote(note_value, safe='')}"
    )
    room_path = (
        f"/r/{quote(room, safe='')}/say-signed/"
        f"{quote(did, safe='')}/{quote(room_signature, safe='')}/{room_nonce}/"
        f"{quote(message, safe='')}"
    )

    return {
        "did": did,
        "fingerprint": fingerprint,
        "repo_url": repo_url,
        "did_note": {
            "namespace": "did",
            "key": fingerprint,
            "nonce": note_nonce,
            "value": note_value,
            "canonical_sha256": sha256_text(note_canonical),
            "signature": note_signature,
            "path": note_path,
        },
        "room_checkin": {
            "room": room,
            "nonce": room_nonce,
            "message": message,
            "canonical_sha256": sha256_text(room_canonical),
            "signature": room_signature,
            "path": room_path,
        },
    }


def register_identity(
    *,
    identity_path: Path,
    proof_path: Path,
    passphrase: str,
    repo_url: str,
    room: str,
    message: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 20.0,
    http_get: HttpGet = default_http_get,
) -> JsonObject:
    identity = load_json(identity_path)
    seed = decrypt_identity(identity, passphrase)
    did = did_from_private_seed(seed)
    note_nonce = next_nonce(identity_path, f"kv:did:{did_fingerprint(did)}")
    room_nonce = next_nonce(identity_path, f"room:{room}")
    payload = build_registration_payload(
        seed=seed,
        repo_url=repo_url,
        room=room,
        message=message,
        note_nonce=note_nonce,
        room_nonce=room_nonce,
    )

    note_status, note_write_body = http_get(base_url, payload["did_note"]["path"], timeout)
    room_status, room_write_body = http_get(base_url, payload["room_checkin"]["path"], timeout)
    note_read_status, note_read_body = http_get(
        base_url,
        f"/kv/did/{quote(payload['fingerprint'], safe='')}",
        timeout,
    )
    room_read_status, room_read_body = http_get(
        base_url,
        f"/r/{quote(payload['room_checkin']['room'], safe='')}?limit=200",
        timeout,
    )

    note_found = payload["did_note"]["value"] in note_read_body
    rendered_key = payload["did"].removeprefix("did:key:")
    room_found = (
        payload["room_checkin"]["message"] in room_read_body
        and rendered_key in room_read_body
    )
    proof: JsonObject = {
        "format": PROOF_FORMAT,
        "version": PROOF_VERSION,
        "generated_at": utc_now(),
        "identity": {
            "did": payload["did"],
            "fingerprint": payload["fingerprint"],
        },
        "contribution": {
            "name": "Technocore iOS Agent Kit",
            "repo_url": payload["repo_url"],
            "platform": "ios",
        },
        "did_note": {
            key: value for key, value in payload["did_note"].items() if key != "path"
        },
        "room_checkin": {
            key: value for key, value in payload["room_checkin"].items() if key != "path"
        },
        "remote": {
            "base_url": _validate_base_url(base_url),
            "did_note_write": {
                "status": note_status,
                "response_sha256": sha256_text(note_write_body),
            },
            "room_write": {
                "status": room_status,
                "response_sha256": sha256_text(room_write_body),
            },
            "did_note_readback": {
                "status": note_read_status,
                "value_found": note_found,
                "response_sha256": sha256_text(note_read_body),
            },
            "room_readback": {
                "status": room_read_status,
                "signed_record_found": room_found,
                "response_sha256": sha256_text(room_read_body),
            },
        },
        "verification": {
            "local_signatures_valid": True,
            "private_key_included": False,
            "remote_write_completed": note_status < 300 and room_status < 300,
            "remote_readback_completed": note_found and room_found,
        },
    }
    errors = verify_proof_data(proof)
    if errors:
        raise ToolError("generated proof failed local verification: " + "; ".join(errors))
    atomic_write_json(proof_path, proof, mode=0o644, forbid_git=False)
    return proof


def verify_proof_data(proof: JsonObject) -> list[str]:
    errors: list[str] = []
    if proof.get("format") != PROOF_FORMAT or proof.get("version") != PROOF_VERSION:
        return ["unsupported proof format or version"]
    identity = proof.get("identity")
    note = proof.get("did_note")
    room = proof.get("room_checkin")
    if not isinstance(identity, dict) or not isinstance(note, dict) or not isinstance(room, dict):
        return ["proof is missing identity, did_note, or room_checkin"]
    did = str(identity.get("did", ""))
    try:
        expected_fingerprint = did_fingerprint(did)
    except ToolError as exc:
        return [str(exc)]
    if identity.get("fingerprint") != expected_fingerprint:
        errors.append("DID fingerprint does not match")
    contribution = proof.get("contribution")
    if not isinstance(contribution, dict):
        errors.append("proof is missing contribution metadata")
        contribution = {}
    repo_url = str(contribution.get("repo_url", ""))
    expected_note_value = f"{did} platform:ios repo:{repo_url}"
    if note.get("namespace") != "did":
        errors.append("DID note namespace must be did")
    if note.get("key") != expected_fingerprint:
        errors.append("DID note key does not match the fingerprint")
    if note.get("value") != expected_note_value:
        errors.append("DID note does not bind this DID to the contribution URL")

    try:
        note_canonical = canonical_note(
            str(note.get("namespace", "")),
            str(note.get("key", "")),
            str(note.get("nonce", "")),
            str(note.get("value", "")),
        )
        verify_canonical(did, note_canonical, str(note.get("signature", "")))
        if note.get("canonical_sha256") != sha256_text(note_canonical):
            errors.append("DID note canonical hash does not match")
    except ToolError as exc:
        errors.append(f"DID note: {exc}")

    try:
        room_canonical = canonical_room(
            str(room.get("room", "")),
            str(room.get("nonce", "")),
            str(room.get("message", "")),
        )
        verify_canonical(did, room_canonical, str(room.get("signature", "")))
        if room.get("canonical_sha256") != sha256_text(room_canonical):
            errors.append("room canonical hash does not match")
    except ToolError as exc:
        errors.append(f"room check-in: {exc}")
    return errors


def scan_for_private_material(root: Path) -> list[str]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise ToolError(f"scan root does not exist: {root}")
    findings: list[str] = []
    banned_exact = {
        ".env",
        "flop_identity.enc.json",
        "technocore_identity.enc.json",
        "technocore_local_state.json",
    }
    banned_suffixes = (".seed", ".pem", ".key", ".p12", ".pfx", ".enc.json")
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules"}
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if name not in skip_dirs]
        for filename in filenames:
            path = Path(directory) / filename
            relative = path.relative_to(root).as_posix()
            lower = filename.lower()
            if lower in banned_exact or lower.endswith(banned_suffixes):
                findings.append(f"private-looking filename: {relative}")
                continue
            if path.suffix.lower() == ".json" and path.stat().st_size <= 1_000_000:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(data, dict) and data.get("format") == IDENTITY_FORMAT:
                    findings.append(f"encrypted identity file must remain off Git: {relative}")
    return findings


def create_example_proof() -> JsonObject:
    seed = hashlib.sha256(b"technocore-ios-agent-example-v1").digest()
    payload = build_registration_payload(
        seed=seed,
        repo_url=DEFAULT_REPO_URL,
        room="example-room",
        message="Example-only signed record; not an eligibility or token claim.",
        note_nonce=1001,
        room_nonce=1002,
    )
    return {
        "format": PROOF_FORMAT,
        "version": PROOF_VERSION,
        "generated_at": "2026-08-24T00:00:00Z",
        "identity": {
            "did": payload["did"],
            "fingerprint": payload["fingerprint"],
        },
        "contribution": {
            "name": "Technocore iOS Agent Kit — example proof",
            "repo_url": DEFAULT_REPO_URL,
            "platform": "ios",
        },
        "did_note": {
            key: value for key, value in payload["did_note"].items() if key != "path"
        },
        "room_checkin": {
            key: value for key, value in payload["room_checkin"].items() if key != "path"
        },
        "remote": {
            "base_url": DEFAULT_BASE_URL,
            "example_only": True,
        },
        "verification": {
            "local_signatures_valid": True,
            "private_key_included": False,
            "remote_write_completed": False,
            "remote_readback_completed": False,
        },
    }


def prompt_new_passphrase() -> str:
    first = getpass.getpass(
        f"New passphrase (minimum {MIN_PASSPHRASE_CHARS} characters): "
    )
    second = getpass.getpass("Repeat passphrase: ")
    if first != second:
        raise ToolError("passphrases do not match")
    if len(first) < MIN_PASSPHRASE_CHARS:
        raise ToolError(
            f"passphrase must contain at least {MIN_PASSPHRASE_CHARS} characters"
        )
    return first


def command_init(args: argparse.Namespace) -> int:
    identity_path = Path(args.identity).expanduser()
    if identity_path.exists() and not args.force:
        raise ToolError(f"identity already exists: {identity_path}; refusing to overwrite")
    if _path_is_inside_git(identity_path):
        raise ToolError("choose an identity path outside every Git working tree")
    passphrase = prompt_new_passphrase()
    seed = secrets.token_bytes(32)
    identity = encrypt_identity(seed, passphrase, label=args.label)
    atomic_write_json(identity_path, identity, mode=0o600, forbid_git=True)
    print("Identity created.")
    print(f"DID: {identity['did']}")
    print(f"Fingerprint: {identity['fingerprint']}")
    print(f"Private identity file: {identity_path.resolve()}")
    print("Back up the encrypted file and store its passphrase separately.")
    return 0


def command_public(args: argparse.Namespace) -> int:
    identity = load_json(Path(args.identity))
    if identity.get("format") != IDENTITY_FORMAT:
        raise ToolError("not a supported identity file")
    public = {
        "format": "technocore-public-identity",
        "version": 1,
        "created_at": identity.get("created_at"),
        "label": identity.get("label", ""),
        "did": identity.get("did"),
        "fingerprint": identity.get("fingerprint"),
    }
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


def command_register(args: argparse.Namespace) -> int:
    identity_path = Path(args.identity).expanduser()
    identity = load_json(identity_path)
    did = str(identity.get("did", ""))
    public_bytes_from_did(did)
    message = args.message or (
        "Technocore iOS agent online. Local key custody and public verification kit: "
        f"{args.repo_url}"
    )
    print("This will publish public, signed data to Technocore:")
    print(f"  DID: {did}")
    print(f"  Room: {args.room}")
    print(f"  Message: {clean_text(message, MAX_MESSAGE_CHARS)}")
    print(f"  Contribution: {args.repo_url}")
    if not args.yes:
        confirmation = input("Type REGISTER to continue: ").strip()
        if confirmation != "REGISTER":
            raise ToolError("registration cancelled")
    passphrase = getpass.getpass("Identity passphrase: ")
    proof = register_identity(
        identity_path=identity_path,
        proof_path=Path(args.proof),
        passphrase=passphrase,
        repo_url=args.repo_url,
        room=args.room,
        message=message,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    verification = proof["verification"]
    print("Registration request completed.")
    print(f"DID: {proof['identity']['did']}")
    print(f"Fingerprint: {proof['identity']['fingerprint']}")
    print(f"Nonce: {proof['room_checkin']['nonce']}")
    print(f"Proof file: {Path(args.proof).expanduser().resolve()}")
    if not verification["remote_readback_completed"]:
        print("WARNING: writes returned successfully, but full readback was not confirmed.")
        return 2
    return 0


def command_verify_proof(args: argparse.Namespace) -> int:
    proof = load_json(Path(args.proof))
    errors = verify_proof_data(proof)
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    print(f"valid proof for {proof['identity']['did']}")
    return 0


def command_scan(args: argparse.Namespace) -> int:
    findings = scan_for_private_material(Path(args.root))
    if findings:
        for finding in findings:
            print(f"SECRET-SCAN: {finding}")
        return 1
    print("secret scan passed")
    return 0


def command_self_test(_: argparse.Namespace) -> int:
    seed = hashlib.sha256(b"technocore-ios-agent-self-test").digest()
    did = did_from_private_seed(seed)
    canonical = canonical_room("self-test", 1, "hello\nworld")
    signature = sign_canonical(seed, canonical)
    verify_canonical(did, canonical, signature)
    identity = encrypt_identity(seed, "correct horse battery staple", label="self-test")
    recovered = decrypt_identity(identity, "correct horse battery staple")
    if recovered != seed:
        raise ToolError("identity encryption round-trip failed")
    proof = create_example_proof()
    errors = verify_proof_data(proof)
    if errors:
        raise ToolError("example proof failed: " + "; ".join(errors))
    print("self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init", help="generate and encrypt a new identity")
    initialize.add_argument("--identity", default=str(default_identity_path()))
    initialize.add_argument("--label", default="")
    initialize.add_argument("--force", action="store_true")
    initialize.set_defaults(handler=command_init)

    public = subparsers.add_parser("public", help="print public identity metadata")
    public.add_argument("--identity", default=str(default_identity_path()))
    public.set_defaults(handler=command_public)

    register = subparsers.add_parser("register", help="publish a signed DID note and room check-in")
    register.add_argument("--identity", default=str(default_identity_path()))
    register.add_argument("--proof", default="technocore_registration_proof.json")
    register.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    register.add_argument("--room", default=DEFAULT_ROOM)
    register.add_argument("--message")
    register.add_argument("--base-url", default=DEFAULT_BASE_URL)
    register.add_argument("--timeout", type=float, default=20.0)
    register.add_argument("--yes", action="store_true")
    register.set_defaults(handler=command_register)

    verify = subparsers.add_parser("verify-proof", help="verify a public proof locally")
    verify.add_argument("proof")
    verify.set_defaults(handler=command_verify_proof)

    scan = subparsers.add_parser("scan", help="fail on private identity material in a tree")
    scan.add_argument("--root", default=".")
    scan.set_defaults(handler=command_scan)

    self_test = subparsers.add_parser("self-test", help="run local cryptographic checks")
    self_test.set_defaults(handler=command_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
