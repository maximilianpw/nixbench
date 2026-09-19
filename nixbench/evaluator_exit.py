from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

try:
    from .scoring import parse_criteria, score_schema_two_payload
except ImportError:  # Direct evaluator invocation by file path.
    from scoring import parse_criteria, score_schema_two_payload


def evaluator_exit_code(metadata_path: Path, score_path: Path) -> int:
    try:
        with metadata_path.open("rb") as handle:
            metadata = tomllib.load(handle)
        criteria = parse_criteria(
            metadata.get("criteria"), max_score=metadata.get("max_score")
        )
        payload = json.loads(score_path.read_text(encoding="utf-8"))
        _, detail = score_schema_two_payload(payload, criteria)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, TypeError):
        return 2
    return 0 if detail["required_passed"] else 1


def main(argv: list[str] | None = None) -> int:
    values = sys.argv[1:] if argv is None else argv
    if len(values) != 2:
        print("usage: python -m nixbench.evaluator_exit METADATA SCORE", file=sys.stderr)
        return 2
    return evaluator_exit_code(Path(values[0]), Path(values[1]))


if __name__ == "__main__":
    raise SystemExit(main())
