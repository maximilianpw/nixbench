from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .adapters import get_trusted_adapter

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


MODEL_IDENTITY_EVIDENCE = {
    "vendor-api-direct",
    "router-alias",
    "local-weights-sha256",
    "unverified",
}
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
CONTROLLED_PROTOCOL_IDENTITY_SCHEMA_VERSION = 1
PROTOCOL_FIELDS = (
    "schema_version",
    "id",
    "harness_id",
    "harness_version",
    "model_id",
    "model_identity_evidence",
    "effort",
    "network_policy",
    "isolation_profile",
    "tool_policy",
    "completion_attestation",
    "agent_adapter",
    "agent_timeout_seconds",
    "system",
)


@dataclass(frozen=True)
class ResolvedProtocol:
    schema_version: int | None
    id: str
    harness_id: str
    harness_version: str
    model_id: str
    model_identity_evidence: str
    effort: str
    network_policy: str
    isolation_profile: str
    tool_policy: str
    completion_attestation: str
    agent_adapter: str | None
    agent_adapter_sha256: str | None
    agent_adapter_bundle_sha256: str | None
    attestation_trust: str
    agent_timeout_seconds: int
    system: str
    wrapper_prompt_sha256: str | None
    agent_command_sha256: str | None
    protocol_complete: bool
    configuration_id: str
    timing_environment_id: str

    def controlled_fields(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "harness_id": self.harness_id,
            "harness_version": self.harness_version,
            "model_id": self.model_id,
            "model_identity_evidence": self.model_identity_evidence,
            "effort": self.effort,
            "network_policy": self.network_policy,
            "isolation_profile": self.isolation_profile,
            "tool_policy": self.tool_policy,
            "completion_attestation": self.completion_attestation,
            "agent_adapter": self.agent_adapter,
            "agent_adapter_sha256": self.agent_adapter_sha256,
            "agent_adapter_bundle_sha256": self.agent_adapter_bundle_sha256,
            "attestation_trust": self.attestation_trust,
            "agent_timeout_seconds": self.agent_timeout_seconds,
            "system": self.system,
            "wrapper_prompt_sha256": self.wrapper_prompt_sha256,
            "agent_command_sha256": self.agent_command_sha256,
        }

    def to_json(self) -> dict[str, object]:
        return {
            **self.controlled_fields(),
            "protocol_complete": self.protocol_complete,
            "configuration_id": self.configuration_id,
            "timing_environment_id": self.timing_environment_id,
        }


def resolve_protocol(
    protocol_path: Path | None,
    *,
    corpus_digest: str,
    agent_command: str | None,
    agent_adapter: str | None = None,
    wrapper_prompt_path: Path | None,
    agent_timeout_seconds: int,
    system: str,
    host: str,
    platform: str,
    legacy_metadata: dict[str, object] | None = None,
) -> ResolvedProtocol:
    if agent_timeout_seconds <= 0:
        raise ValueError("agent timeout must be a positive integer")
    wrapper_hash = _hash_file(wrapper_prompt_path) if wrapper_prompt_path else None
    command_hash = _sha256(agent_command.encode("utf-8")) if agent_command else None

    if protocol_path is None:
        legacy = legacy_metadata or {}
        values: dict[str, object] = {
            "schema_version": None,
            "id": "legacy-incomplete",
            "harness_id": "nixbench",
            "harness_version": "unverified",
            "model_id": _legacy_string(legacy.get("model"), "unverified"),
            "model_identity_evidence": "unverified",
            "effort": _legacy_string(legacy.get("effort"), "unverified"),
            "network_policy": _legacy_string(legacy.get("network"), "unknown"),
            "isolation_profile": "unverified",
            "tool_policy": "unverified",
            "completion_attestation": "unattested",
            "agent_adapter": None,
            "agent_timeout_seconds": agent_timeout_seconds,
            "system": system,
        }
        complete = False
        adapter_digest = None
        adapter_bundle_digest = None
        attestation_trust = "unattested"
    else:
        values = _load_protocol(protocol_path)
        if values["agent_timeout_seconds"] != agent_timeout_seconds:
            raise ValueError(
                "protocol agent_timeout_seconds does not match --agent-timeout-seconds"
            )
        if values["system"] != system:
            raise ValueError("protocol system does not match --system")
        selected_adapter = values["agent_adapter"]
        if agent_adapter is not None and agent_adapter != selected_adapter:
            raise ValueError("--agent-adapter does not match protocol agent_adapter")
        if agent_adapter is None:
            values["completion_attestation"] = "unattested"
            values["agent_adapter"] = None
            adapter_digest = None
            adapter_bundle_digest = None
            attestation_trust = "unattested"
            complete = False
        else:
            adapter = get_trusted_adapter(agent_adapter)
            adapter_isolation = getattr(adapter, "isolation_profile", None)
            if adapter_isolation is not None and values["isolation_profile"] != adapter_isolation:
                raise ValueError(
                    "protocol isolation_profile does not match the trusted adapter"
                )
            if (
                values["isolation_profile"] == "linux-bwrap-v1"
                and adapter_isolation != "linux-bwrap-v1"
            ):
                raise ValueError(
                    "linux-bwrap-v1 requires the matching trusted isolation adapter"
                )
            adapter_digest = adapter.sha256
            adapter_bundle_digest = adapter.bundle_sha256
            attestation_trust = adapter.trust
            if agent_command is None:
                raise ValueError("a complete protocol requires --agent-cmd")
            if wrapper_prompt_path is None:
                raise ValueError("a complete protocol requires --wrapper-prompt-file")
            complete = True
        supplied = legacy_metadata or {}
        for cli_field, protocol_field in (
            ("model", "model_id"),
            ("effort", "effort"),
            ("network", "network_policy"),
        ):
            cli_value = supplied.get(cli_field)
            if cli_value is not None and cli_value != values[protocol_field]:
                raise ValueError(
                    f"--{cli_field.replace('_', '-')} does not match protocol {protocol_field}"
                )

    controlled = {
        **values,
        "wrapper_prompt_sha256": wrapper_hash,
        "agent_command_sha256": command_hash,
        "agent_adapter_sha256": adapter_digest,
        "agent_adapter_bundle_sha256": adapter_bundle_digest,
        "attestation_trust": attestation_trust,
    }
    configuration_id = compute_configuration_id(corpus_digest, controlled)
    timing_environment_id = "timing-" + _hash_json(
        {
            "host": host,
            "platform": platform,
            "system": system,
            "isolation_profile": controlled["isolation_profile"],
        }
    )
    return ResolvedProtocol(
        schema_version=controlled["schema_version"],  # type: ignore[arg-type]
        id=str(controlled["id"]),
        harness_id=str(controlled["harness_id"]),
        harness_version=str(controlled["harness_version"]),
        model_id=str(controlled["model_id"]),
        model_identity_evidence=str(controlled["model_identity_evidence"]),
        effort=str(controlled["effort"]),
        network_policy=str(controlled["network_policy"]),
        isolation_profile=str(controlled["isolation_profile"]),
        tool_policy=str(controlled["tool_policy"]),
        completion_attestation=str(controlled["completion_attestation"]),
        agent_adapter=(
            str(controlled["agent_adapter"])
            if controlled["agent_adapter"] is not None
            else None
        ),
        agent_adapter_sha256=adapter_digest,
        agent_adapter_bundle_sha256=adapter_bundle_digest,
        attestation_trust=attestation_trust,
        agent_timeout_seconds=int(controlled["agent_timeout_seconds"]),
        system=str(controlled["system"]),
        wrapper_prompt_sha256=wrapper_hash,
        agent_command_sha256=command_hash,
        protocol_complete=complete,
        configuration_id=configuration_id,
        timing_environment_id=timing_environment_id,
    )


def compute_configuration_id(
    corpus_digest: str, controlled_protocol: dict[str, object]
) -> str:
    """Return the canonical identity for a corpus and controlled protocol payload."""
    return "cfg-" + _hash_json(
        {"corpus_digest": corpus_digest, "protocol": controlled_protocol}
    )


def _load_protocol(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"protocol file does not exist or is not a file: {path}")
    try:
        with path.open("rb") as handle:
            protocol = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read protocol file {path}: {exc}") from exc

    schema_version = protocol.get("schema_version")
    if type(schema_version) is not int or schema_version not in {1, 2}:
        raise ValueError("protocol schema_version must be 1 or 2")
    expected = set(PROTOCOL_FIELDS)
    if schema_version == 1:
        expected.remove("agent_adapter")
    missing = sorted(expected - protocol.keys())
    unknown = sorted(protocol.keys() - expected)
    if missing:
        raise ValueError(f"protocol is missing fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"protocol has unknown fields: {', '.join(unknown)}")
    protocol.setdefault("agent_adapter", None)
    for field in PROTOCOL_FIELDS:
        if field not in expected:
            continue
        if field in {"schema_version", "agent_timeout_seconds"}:
            continue
        value = protocol[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"protocol {field} must be a non-empty string")
    for field in ("id", "harness_id"):
        value = str(protocol[field])
        if ID_PATTERN.fullmatch(value) is None:
            raise ValueError(f"protocol {field} contains unsupported characters")
    evidence = protocol["model_identity_evidence"]
    if evidence not in MODEL_IDENTITY_EVIDENCE:
        choices = ", ".join(sorted(MODEL_IDENTITY_EVIDENCE))
        raise ValueError(f"model_identity_evidence must be one of: {choices}")
    if protocol["completion_attestation"] != "required":
        raise ValueError("complete protocol completion_attestation must be required")
    timeout = protocol["agent_timeout_seconds"]
    if type(timeout) is not int or timeout <= 0:
        raise ValueError("protocol agent_timeout_seconds must be a positive integer")
    return protocol


def _hash_file(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"wrapper prompt file does not exist or is not a file: {path}")
    try:
        return _sha256(path.read_bytes())
    except OSError as exc:
        raise ValueError(f"cannot read wrapper prompt file {path}: {exc}") from exc


def _hash_json(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _sha256(encoded)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _legacy_string(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default
