"""One-time reviewed source transformation for PR #1.

The script is removed from the branch after it applies the exact replacements.
It exists only because the connected GitHub surface writes whole files rather
than unified patches.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "technocore_agent.py"
TESTS = ROOT / "tests" / "test_technocore_agent.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {text.count(old)}")
    return text.replace(old, new, 1)


core = CORE.read_text(encoding="utf-8")
core = replace_once(core, "import os\nimport secrets\n", "import os\nimport re\nimport secrets\n", "import re")
core = replace_once(
    core,
    'USER_AGENT = "technocore-ios-agent/1.0"\n',
    'USER_AGENT = "technocore-ios-agent/1.0"\n'
    'ROOM_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")\n',
    "room regex",
)
core = replace_once(
    core,
    '''    if kdf.get("name") != "scrypt" or cipher.get("name") != "aes-256-gcm":
        raise ToolError("identity file uses unsupported encryption")
    salt = b64url_decode(str(kdf.get("salt", "")))
    nonce = b64url_decode(str(cipher.get("nonce", "")))
    ciphertext = b64url_decode(str(cipher.get("ciphertext", "")))
    key = _derive_encryption_key(
        passphrase,
        salt,
        n=int(kdf.get("n", 0)),
        r=int(kdf.get("r", 0)),
        p=int(kdf.get("p", 0)),
    )
''',
    '''    if kdf.get("name") != "scrypt" or cipher.get("name") != "aes-256-gcm":
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
''',
    "scrypt validation",
)
core = replace_once(
    core,
    '''def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.params or parsed.query or parsed.fragment:
        raise ToolError("base URL must be a plain HTTPS origin")
    if parsed.path not in ("", "/"):
        raise ToolError("base URL must not contain a path")
    return base_url.rstrip("/")
''',
    '''def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.params or parsed.query or parsed.fragment:
        raise ToolError("base URL must be a plain HTTPS origin")
    if parsed.username or parsed.password:
        raise ToolError("base URL must not contain credentials")
    if parsed.path not in ("", "/"):
        raise ToolError("base URL must not contain a path")
    return base_url.rstrip("/")
''',
    "HTTPS origin validation",
)
core = replace_once(
    core,
    '''    room = clean_text(room, 48)
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in room):
        raise ToolError("room name must use lowercase letters, digits, underscore, or hyphen")
''',
    '''    room = clean_text(room, 48)
    if not ROOM_RE.fullmatch(room):
        raise ToolError(
            "room name must be 1-48 lowercase letters, digits, underscores, or hyphens "
            "and start with a letter or digit"
        )
''',
    "room name validation",
)
core = replace_once(
    core,
    '''    room_found = (
        payload["room_checkin"]["message"] in room_read_body
        and payload["did"] in room_read_body
    )
''',
    '''    rendered_key = payload["did"].removeprefix("did:key:")
    room_found = (
        payload["room_checkin"]["message"] in room_read_body
        and rendered_key in room_read_body
    )
''',
    "signed writer readback",
)
core = replace_once(
    core,
    '''    if identity.get("fingerprint") != expected_fingerprint:
        errors.append("DID fingerprint does not match")

    try:
        note_canonical = canonical_note(
''',
    '''    if identity.get("fingerprint") != expected_fingerprint:
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
''',
    "proof binding",
)
CORE.write_text(core, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    '''        with self.assertRaises(agent.ToolError):
            agent.decrypt_identity(identity, "this is the wrong passphrase")
''',
    '''        with self.assertRaises(agent.ToolError):
            agent.decrypt_identity(identity, "this is the wrong passphrase")
        identity["kdf"]["n"] = agent.KDF_N * 2
        with self.assertRaisesRegex(agent.ToolError, "unsupported scrypt parameters"):
            agent.decrypt_identity(identity, self.passphrase)
''',
    "KDF regression test",
)
tests = replace_once(
    tests,
    '''    def test_example_proof_verifies(self) -> None:
        proof = agent.create_example_proof()
        self.assertEqual(agent.verify_proof_data(proof), [])
        proof["room_checkin"]["message"] = "tampered"
        self.assertTrue(agent.verify_proof_data(proof))
''',
    '''    def test_example_proof_verifies(self) -> None:
        proof = agent.create_example_proof()
        self.assertEqual(agent.verify_proof_data(proof), [])
        proof["room_checkin"]["message"] = "tampered"
        self.assertTrue(agent.verify_proof_data(proof))

    def test_proof_binds_the_contribution_url(self) -> None:
        proof = agent.create_example_proof()
        proof["contribution"]["repo_url"] = "https://example.com/other"
        errors = agent.verify_proof_data(proof)
        self.assertTrue(any("contribution URL" in error for error in errors))

    def test_room_name_matches_the_server_rule(self) -> None:
        with self.assertRaises(agent.ToolError):
            agent.build_registration_payload(
                seed=self.seed,
                repo_url="https://example.com/repo",
                room="-invalid",
                message="hello",
                note_nonce=1,
                room_nonce=2,
            )
''',
    "proof and room regression tests",
)
tests = replace_once(
    tests,
    '''                    return 200, f"[1 now] <{identity['did']}> {message}\\n"
''',
    '''                    rendered_key = identity["did"].removeprefix("did:key:")
                    return 200, f"[1 now] <{rendered_key}> {message}\\n"
''',
    "live readback fixture",
)
TESTS.write_text(tests, encoding="utf-8")

Path(__file__).unlink()
