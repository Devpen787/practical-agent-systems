#!/usr/bin/env python3
"""Tap-to-run menu for Pyto on iPhone or iPad."""

from __future__ import annotations

from pathlib import Path

import technocore_agent as agent


def choose(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def main() -> int:
    print("Technocore iOS Agent Kit")
    print("1. Self-test")
    print("2. Create encrypted identity")
    print("3. Show public identity")
    print("4. Register signed contribution")
    print("5. Verify public proof")
    selection = input("Choose 1-5: ").strip()

    identity = str(agent.default_identity_path())
    if selection == "1":
        return agent.main(["self-test"])
    if selection == "2":
        label = input("Public identity label (optional): ").strip()
        arguments = ["init", "--identity", identity]
        if label:
            arguments += ["--label", label]
        return agent.main(arguments)
    if selection == "3":
        return agent.main(["public", "--identity", identity])
    if selection == "4":
        proof = choose(
            "Public proof output",
            str(Path.home() / "Documents" / "technocore_registration_proof.json"),
        )
        repo_url = choose("Contribution URL", agent.DEFAULT_REPO_URL)
        return agent.main(
            [
                "register",
                "--identity",
                identity,
                "--proof",
                proof,
                "--repo-url",
                repo_url,
            ]
        )
    if selection == "5":
        proof = input("Path to proof JSON: ").strip()
        if not proof:
            print("A proof path is required.")
            return 1
        return agent.main(["verify-proof", proof])
    print("Unknown selection.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
