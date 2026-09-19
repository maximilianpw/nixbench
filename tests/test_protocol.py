from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nixbench.protocol import resolve_protocol


class ProtocolTests(unittest.TestCase):
    def test_equivalent_toml_key_order_has_same_configuration_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_bytes(b"exact prompt\n")
            first = root / "first.toml"
            second = root / "second.toml"
            values = protocol_values()
            first.write_text("\n".join(values) + "\n")
            second.write_text("\n".join(reversed(values)) + "\n")

            first_resolved = resolve(first, wrapper)
            second_resolved = resolve(second, wrapper)

            self.assertEqual(
                first_resolved.configuration_id, second_resolved.configuration_id
            )
            self.assertTrue(first_resolved.protocol_complete)

    def test_behavior_fields_change_configuration_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            base_path = root / "base.toml"
            base_path.write_text("\n".join(protocol_values()) + "\n")
            base = resolve(base_path, wrapper)

            changes = {
                'id = "test-profile"': 'id = "other-profile"',
                'harness_id = "nixbench"': 'harness_id = "other-harness"',
                'model_id = "model-a"': 'model_id = "model-b"',
                'harness_version = "1.0"': 'harness_version = "1.1"',
                'model_identity_evidence = "vendor-api-direct"': 'model_identity_evidence = "router-alias"',
                'effort = "high"': 'effort = "medium"',
                'network_policy = "disabled"': 'network_policy = "enabled"',
                'isolation_profile = "test"': 'isolation_profile = "isolated"',
                'tool_policy = "test"': 'tool_policy = "restricted"',
            }
            for index, (old, new) in enumerate(changes.items()):
                changed_path = root / f"changed-{index}.toml"
                changed_path.write_text(base_path.read_text().replace(old, new))
                self.assertNotEqual(
                    base.configuration_id,
                    resolve(changed_path, wrapper).configuration_id,
                )

            self.assertNotEqual(
                base.configuration_id,
                resolve(
                    base_path, wrapper, command="agent --different"
                ).configuration_id,
            )
            wrapper.write_text("changed prompt")
            self.assertNotEqual(
                base.configuration_id, resolve(base_path, wrapper).configuration_id
            )
            self.assertNotEqual(
                base.configuration_id,
                resolve(base_path, wrapper, corpus_digest="b" * 64).configuration_id,
            )
            system_path = root / "system.toml"
            system_path.write_text(
                base_path.read_text().replace("x86_64-linux", "aarch64-linux")
            )
            self.assertNotEqual(
                base.configuration_id,
                resolve(system_path, wrapper, system="aarch64-linux").configuration_id,
            )

    def test_timeout_change_requires_actual_timeout_to_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text(
                ("\n".join(protocol_values()) + "\n").replace(
                    "agent_timeout_seconds = 300", "agent_timeout_seconds = 301"
                )
            )

            changed = resolve(path, wrapper, timeout=301)
            baseline_path = root / "baseline.toml"
            baseline_path.write_text("\n".join(protocol_values()) + "\n")
            baseline = resolve(baseline_path, wrapper)

            self.assertNotEqual(baseline.configuration_id, changed.configuration_id)

    def test_display_metadata_does_not_change_configuration_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")

            first = resolve_protocol(
                path,
                corpus_digest="a" * 64,
                agent_command="agent",
                agent_adapter="codex-json",
                wrapper_prompt_path=wrapper,
                agent_timeout_seconds=300,
                system="x86_64-linux",
                host="host",
                platform="platform",
                legacy_metadata={"series": "one", "label": "One"},
            )
            second = resolve_protocol(
                path,
                corpus_digest="a" * 64,
                agent_command="agent",
                agent_adapter="codex-json",
                wrapper_prompt_path=wrapper,
                agent_timeout_seconds=300,
                system="x86_64-linux",
                host="host",
                platform="platform",
                legacy_metadata={"series": "two", "label": "Two"},
            )

            self.assertEqual(first.configuration_id, second.configuration_id)

    def test_host_changes_timing_identity_not_configuration_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")

            first = resolve(path, wrapper, host="one")
            second = resolve(path, wrapper, host="two")

            self.assertEqual(first.configuration_id, second.configuration_id)
            self.assertNotEqual(
                first.timing_environment_id, second.timing_environment_id
            )

    def test_self_asserted_hashes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text(
                "\n".join(protocol_values())
                + '\nwrapper_prompt_sha256 = "self-asserted"\n'
            )

            with self.assertRaisesRegex(ValueError, "unknown fields"):
                resolve(path, wrapper)

    def test_missing_protocol_is_explicitly_incomplete(self) -> None:
        resolved = resolve_protocol(
            None,
            corpus_digest="a" * 64,
            agent_command="agent",
            wrapper_prompt_path=None,
            agent_timeout_seconds=300,
            system="x86_64-linux",
            host="host",
            platform="platform",
            legacy_metadata={"model": "legacy-model", "effort": "high"},
        )

        self.assertFalse(resolved.protocol_complete)
        self.assertEqual(resolved.model_id, "legacy-model")
        self.assertEqual(resolved.completion_attestation, "unattested")

    def test_raw_agent_command_cannot_complete_a_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")

            resolved = resolve_protocol(
                path,
                corpus_digest="a" * 64,
                agent_command='printf status > "$NIXBENCH_AGENT_STATUS_FILE"',
                agent_adapter=None,
                wrapper_prompt_path=wrapper,
                agent_timeout_seconds=300,
                system="x86_64-linux",
                host="host",
                platform="platform",
            )

            self.assertFalse(resolved.protocol_complete)
            self.assertEqual(resolved.completion_attestation, "unattested")
            self.assertIsNone(resolved.agent_adapter_sha256)

    def test_schema_one_protocol_without_adapter_remains_readable_but_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "legacy.toml"
            path.write_text(
                "\n".join(
                    line
                    for line in protocol_values()
                    if not line.startswith("agent_adapter =")
                ).replace("schema_version = 2", "schema_version = 1")
                + "\n"
            )

            resolved = resolve_protocol(
                path,
                corpus_digest="a" * 64,
                agent_command="agent",
                wrapper_prompt_path=wrapper,
                agent_timeout_seconds=300,
                system="x86_64-linux",
                host="host",
                platform="platform",
            )

            self.assertFalse(resolved.protocol_complete)
            self.assertIsNone(resolved.agent_adapter)

    def test_registered_adapter_digest_is_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")

            resolved = resolve(path, wrapper)

            self.assertEqual(resolved.agent_adapter, "codex-json")
            self.assertRegex(resolved.agent_adapter_sha256 or "", r"^[0-9a-f]{64}$")

    def test_bwrap_adapter_requires_matching_isolation_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            text = "\n".join(protocol_values()) + "\n"
            text = text.replace('agent_adapter = "codex-json"', 'agent_adapter = "codex-json-bwrap"')
            path.write_text(text)

            with self.assertRaisesRegex(ValueError, "isolation_profile"):
                resolve_protocol(
                    path,
                    corpus_digest="a" * 64,
                    agent_command="codex exec --json",
                    agent_adapter="codex-json-bwrap",
                    wrapper_prompt_path=wrapper,
                    agent_timeout_seconds=300,
                    system="x86_64-linux",
                    host="host",
                    platform="linux",
                )

            path.write_text(text.replace('isolation_profile = "test"', 'isolation_profile = "linux-bwrap-v1"'))
            resolved = resolve_protocol(
                path,
                corpus_digest="a" * 64,
                agent_command="codex exec --json",
                agent_adapter="codex-json-bwrap",
                wrapper_prompt_path=wrapper,
                agent_timeout_seconds=300,
                system="x86_64-linux",
                host="host",
                platform="linux",
            )

            self.assertTrue(resolved.protocol_complete)
            self.assertEqual(resolved.attestation_trust, "approved-linux-bwrap-v1")

    def test_adapter_digest_and_trust_change_configuration_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")
            baseline = resolve(path, wrapper)

            for digest, trust in (("f" * 64, baseline.attestation_trust), (baseline.agent_adapter_sha256, "isolated-approved")):
                with self.subTest(digest=digest, trust=trust), patch(
                    "nixbench.protocol.get_trusted_adapter",
                    return_value=SimpleNamespace(sha256=digest, trust=trust),
                ):
                    changed = resolve(path, wrapper)
                self.assertNotEqual(baseline.configuration_id, changed.configuration_id)

    def test_complete_protocol_rejects_conflicting_cli_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrapper = root / "prompt.txt"
            wrapper.write_text("prompt")
            path = root / "protocol.toml"
            path.write_text("\n".join(protocol_values()) + "\n")

            for field, value, message in (
                ("model", "model-b", "model_id"),
                ("effort", "low", "effort"),
                ("network", "enabled", "network_policy"),
            ):
                with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, message
                ):
                    resolve_protocol(
                        path,
                        corpus_digest="a" * 64,
                        agent_command="agent",
                        agent_adapter="codex-json",
                        wrapper_prompt_path=wrapper,
                        agent_timeout_seconds=300,
                        system="x86_64-linux",
                        host="host",
                        platform="platform",
                        legacy_metadata={field: value},
                    )


def resolve(
    path: Path,
    wrapper: Path,
    *,
    command: str = "agent",
    corpus_digest: str = "a" * 64,
    timeout: int = 300,
    host: str = "host",
    system: str = "x86_64-linux",
):
    return resolve_protocol(
        path,
        corpus_digest=corpus_digest,
        agent_command=command,
        agent_adapter="codex-json",
        wrapper_prompt_path=wrapper,
        agent_timeout_seconds=timeout,
        system=system,
        host=host,
        platform="platform",
    )


def protocol_values() -> list[str]:
    return [
        "schema_version = 2",
        'id = "test-profile"',
        'harness_id = "nixbench"',
        'harness_version = "1.0"',
        'model_id = "model-a"',
        'model_identity_evidence = "vendor-api-direct"',
        'effort = "high"',
        'network_policy = "disabled"',
        'isolation_profile = "test"',
        'tool_policy = "test"',
        'completion_attestation = "required"',
        'agent_adapter = "codex-json"',
        "agent_timeout_seconds = 300",
        'system = "x86_64-linux"',
    ]


if __name__ == "__main__":
    unittest.main()
