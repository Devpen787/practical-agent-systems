from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import technocore_agent as agent


class TechnocoreAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = hashlib.sha256(b"unit-test-seed").digest()
        self.passphrase = "correct horse battery staple"

    def test_did_and_signature_round_trip(self) -> None:
        did = agent.did_from_private_seed(self.seed)
        self.assertTrue(did.startswith("did:key:z6Mk"))
        canonical = agent.canonical_room("test-room", 123, "hello\nworld")
        signature = agent.sign_canonical(self.seed, canonical)
        agent.verify_canonical(did, canonical, signature)
        self.assertEqual(agent.did_from_public_bytes(agent.public_bytes_from_did(did)), did)

    def test_encrypted_identity_round_trip(self) -> None:
        identity = agent.encrypt_identity(self.seed, self.passphrase, label="unit test")
        self.assertNotIn(self.seed.hex(), json.dumps(identity))
        self.assertEqual(agent.decrypt_identity(identity, self.passphrase), self.seed)
        with self.assertRaises(agent.ToolError):
            agent.decrypt_identity(identity, "this is the wrong passphrase")
        identity["kdf"]["n"] = agent.KDF_N * 2
        with self.assertRaisesRegex(agent.ToolError, "unsupported scrypt parameters"):
            agent.decrypt_identity(identity, self.passphrase)

    def test_private_identity_refuses_git_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            path = root / "private" / "technocore_identity.enc.json"
            with self.assertRaises(agent.ToolError):
                agent.atomic_write_json(path, {"format": agent.IDENTITY_FORMAT}, forbid_git=True)

    def test_nonce_is_monotonic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "identity.json"
            first = agent.next_nonce(identity_path, "room:lobby")
            second = agent.next_nonce(identity_path, "room:lobby")
            self.assertGreater(second, first)

    def test_example_proof_verifies(self) -> None:
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

    def test_secret_scan_catches_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity = agent.encrypt_identity(self.seed, self.passphrase)
            (root / "accidental.json").write_text(json.dumps(identity), encoding="utf-8")
            findings = agent.scan_for_private_material(root)
            self.assertEqual(len(findings), 1)
            self.assertIn("encrypted identity", findings[0])

    def test_registration_flow_uses_public_proof_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity_path = root / "private" / "identity.json"
            proof_path = root / "public-proof.json"
            identity = agent.encrypt_identity(self.seed, self.passphrase)
            agent.atomic_write_json(identity_path, identity, forbid_git=True)

            calls: list[str] = []

            def fake_get(base_url: str, path: str, timeout: float) -> tuple[int, str]:
                del base_url, timeout
                calls.append(path)
                if path.startswith("/kv/did/") and "/set-signed/" not in path:
                    value = f"{identity['did']} platform:ios repo:https://example.com/repo"
                    return 200, f"# untrusted\n\n{value}\n"
                if path.startswith("/r/lobby?"):
                    message = (
                        "Technocore iOS agent online. Local key custody and public verification kit: "
                        "https://example.com/repo"
                    )
                    rendered_key = identity["did"].removeprefix("did:key:")
                    return 200, f"[1 now] <{rendered_key}> {message}\n"
                return 200, "Written.\n"

            proof = agent.register_identity(
                identity_path=identity_path,
                proof_path=proof_path,
                passphrase=self.passphrase,
                repo_url="https://example.com/repo",
                room="lobby",
                message=(
                    "Technocore iOS agent online. Local key custody and public verification kit: "
                    "https://example.com/repo"
                ),
                http_get=fake_get,
            )
            self.assertTrue(proof["verification"]["remote_readback_completed"])
            self.assertEqual(agent.verify_proof_data(proof), [])
            proof_text = proof_path.read_text(encoding="utf-8")
            self.assertNotIn(self.seed.hex(), proof_text)
            self.assertNotIn("ciphertext", proof_text)
            self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()
