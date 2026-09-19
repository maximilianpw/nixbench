from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence


CRITERION_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FAILURE_CLASSES = {
    "syntax",
    "evaluation",
    "missing-attr",
    "wrong-value",
    "unavailable-helper",
    "impurity",
    "overfit",
    "maintainability",
    "formatting",
}
SUPPLEMENTAL_FAILURE_CLASSES = {"maintainability", "formatting"}
MAX_NOTES = 50
MAX_NOTE_LENGTH = 1_000


@dataclass(frozen=True)
class Criterion:
    id: str
    points: float
    required: bool
    failure_class: str


def parse_criteria(raw: object, *, max_score: float) -> tuple[Criterion, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not raw:
        raise ValueError("criteria must be a non-empty array of tables")

    criteria: list[Criterion] = []
    seen: set[str] = set()
    total = Decimal(0)
    for index, value in enumerate(raw):
        label = f"criteria[{index}]"
        if not isinstance(value, dict):
            raise ValueError(f"{label} must be a table")
        expected_fields = {"id", "points", "required", "failure_class"}
        missing = sorted(expected_fields - value.keys())
        unknown = sorted(value.keys() - expected_fields)
        if missing:
            raise ValueError(f"{label} is missing fields: {', '.join(missing)}")
        if unknown:
            raise ValueError(f"{label} has unknown fields: {', '.join(unknown)}")

        criterion_id = value["id"]
        if (
            not isinstance(criterion_id, str)
            or CRITERION_ID_PATTERN.fullmatch(criterion_id) is None
        ):
            raise ValueError(f"{label}.id must be a lowercase slug")
        if criterion_id in seen:
            raise ValueError(f"duplicate criterion id: {criterion_id}")
        seen.add(criterion_id)

        points = value["points"]
        if not _is_positive_finite_number(points):
            raise ValueError(f"{label}.points must be a positive finite number")
        try:
            total += Decimal(str(points))
        except InvalidOperation as exc:
            raise ValueError(f"{label}.points must be a finite decimal") from exc

        required = value["required"]
        if type(required) is not bool:
            raise ValueError(f"{label}.required must be boolean")

        failure_class = value["failure_class"]
        if failure_class not in FAILURE_CLASSES:
            choices = ", ".join(sorted(FAILURE_CLASSES))
            raise ValueError(f"{label}.failure_class must be one of: {choices}")
        if not required and failure_class not in SUPPLEMENTAL_FAILURE_CLASSES:
            raise ValueError(
                f"{label} may be optional only for formatting or maintainability"
            )

        criteria.append(
            Criterion(
                id=criterion_id,
                points=float(points),
                required=required,
                failure_class=str(failure_class),
            )
        )

    try:
        expected_total = Decimal(str(max_score))
    except InvalidOperation as exc:
        raise ValueError("max_score must be a finite decimal") from exc
    if total != expected_total:
        raise ValueError(f"criterion points must sum exactly to max_score ({max_score})")
    if not any(
        criterion.required
        and criterion.failure_class not in SUPPLEMENTAL_FAILURE_CLASSES
        for criterion in criteria
    ):
        raise ValueError("criteria must include a required functional criterion")
    return tuple(criteria)


def score_schema_two_payload(
    payload: object,
    criteria: Sequence[Criterion],
) -> tuple[float, dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        raise ValueError("criteria-v2 task requires schema_version 2")
    allowed_fields = {"schema_version", "criteria", "notes"}
    unknown_fields = sorted(payload.keys() - allowed_fields)
    if unknown_fields:
        raise ValueError(
            f"schema-version 2 score has unknown fields: {', '.join(unknown_fields)}"
        )
    outcomes = payload.get("criteria")
    if not isinstance(outcomes, dict):
        raise ValueError("schema-version 2 criteria must be an object")
    expected_ids = {criterion.id for criterion in criteria}
    actual_ids = set(outcomes)
    missing = sorted(expected_ids - actual_ids)
    unknown = sorted(actual_ids - expected_ids)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing criteria: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown criteria: {', '.join(unknown)}")
        raise ValueError("; ".join(parts))
    if not all(type(outcomes[criterion.id]) is bool for criterion in criteria):
        raise ValueError("criterion outcomes must be boolean")

    notes = payload.get("notes", [])
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        raise ValueError("score notes must be a list of strings")
    normalized_notes = [note[:MAX_NOTE_LENGTH] for note in notes[:MAX_NOTES]]
    failed = [criterion for criterion in criteria if not outcomes[criterion.id]]
    failure_classes = list(dict.fromkeys(criterion.failure_class for criterion in failed))
    score = sum(criterion.points for criterion in criteria if outcomes[criterion.id])
    normalized_outcomes = {criterion.id: outcomes[criterion.id] for criterion in criteria}
    return score, {
        "format": "criteria-v2",
        "schema_version": 2,
        "criteria": normalized_outcomes,
        "criterion_points": {
            criterion.id: criterion.points for criterion in criteria
        },
        "criterion_failure_classes": {
            criterion.id: criterion.failure_class for criterion in criteria
        },
        "required_criteria": [
            criterion.id for criterion in criteria if criterion.required
        ],
        "failed_criteria": [criterion.id for criterion in failed],
        "failure_classes": failure_classes,
        "required_passed": all(
            outcomes[criterion.id] for criterion in criteria if criterion.required
        ),
        "notes": normalized_notes,
    }


def _is_positive_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False
