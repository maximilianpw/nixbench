from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .task import Task, iter_tasks


CORPUS_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VALID_VISIBILITIES = {"public", "private-heldout", "retired"}


@dataclass(frozen=True)
class CorpusIdentity:
    schema_version: int
    id: str
    version: str
    visibility: str
    digest: str
    task_count: int
    task_ids: tuple[str, ...]
    task_digests: dict[str, str]

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "version": self.version,
            "visibility": self.visibility,
            "digest": self.digest,
            "task_count": self.task_count,
            "task_ids": list(self.task_ids),
            "task_digests": dict(self.task_digests),
        }


def identify_corpus(
    tasks_dir: Path, manifest_path: Path | None = None
) -> CorpusIdentity:
    tasks_dir = tasks_dir.absolute()
    if manifest_path is None:
        adjacent_manifest = tasks_dir.parent / "corpus.toml"
        contained_manifest = tasks_dir / "corpus.toml"
        manifest_path = (
            adjacent_manifest if adjacent_manifest.is_file() else contained_manifest
        )
    manifest_path = manifest_path.absolute()
    corpus_root = manifest_path.parent.resolve()
    _require_regular_file(manifest_path, corpus_root, "corpus manifest")
    tasks_dir = _require_directory_root(tasks_dir, corpus_root, "tasks directory")
    _reject_symlinked_task_roots(tasks_dir)
    manifest = _load_manifest(manifest_path)
    tasks = sorted(iter_tasks(tasks_dir), key=lambda task: task.id)
    if not tasks:
        raise ValueError(f"corpus contains no tasks: {tasks_dir}")

    manifest_entries = tuple(
        (key, str(manifest[key]).encode("utf-8"))
        for key in ("schema_version", "id", "version", "visibility")
    )
    task_digests: dict[str, str] = {}
    corpus_hasher = _CanonicalHasher("nixbench-corpus-v1")
    for key, value in manifest_entries:
        corpus_hasher.add_value(f"manifest/{key}", value)

    contracts_root = corpus_root / "contracts"
    if contracts_root.exists() or contracts_root.is_symlink():
        contracts_root = _require_directory_root(
            contracts_root, corpus_root, "contracts directory"
        )
    for task in tasks:
        task_entries = list(_task_entries(task, corpus_root))
        task_contracts = contracts_root / task.id
        if task_contracts.exists() or task_contracts.is_symlink():
            task_entries.extend(
                _tree_entries(
                    task_contracts, corpus_root, prefix=Path("contracts") / task.id
                )
            )
        task_entries.sort(key=lambda entry: entry[0])

        task_hasher = _CanonicalHasher("nixbench-task-v1")
        task_hasher.add_value("task/id", task.id.encode("utf-8"))
        for path, kind, executable, payload in task_entries:
            task_hasher.add_file(path, kind, executable, payload)
            corpus_hasher.add_file(path, kind, executable, payload)
        task_digest = task_hasher.hexdigest()
        task_digests[task.id] = task_digest
        corpus_hasher.add_value(f"task-digest/{task.id}", task_digest.encode("ascii"))

    if contracts_root.exists():
        known_task_contract_roots = {contracts_root / task.id for task in tasks}
        for child in contracts_root.iterdir():
            if child not in known_task_contract_roots:
                raise ValueError(
                    f"contracts directory does not match a task ID: {child}"
                )

    task_ids = tuple(task.id for task in tasks)
    return CorpusIdentity(
        schema_version=int(manifest["schema_version"]),
        id=str(manifest["id"]),
        version=str(manifest["version"]),
        visibility=str(manifest["visibility"]),
        digest=corpus_hasher.hexdigest(),
        task_count=len(tasks),
        task_ids=task_ids,
        task_digests=task_digests,
    )


class _CanonicalHasher:
    def __init__(self, domain: str) -> None:
        self._hash = hashlib.sha256()
        self.add_value("domain", domain.encode("ascii"))

    def add_value(self, label: str, payload: bytes) -> None:
        self._add_bytes(label.encode("utf-8"))
        self._add_bytes(payload)

    def add_file(self, path: str, kind: str, executable: bool, payload: bytes) -> None:
        self._add_bytes(b"file")
        self._add_bytes(path.encode("utf-8"))
        self._add_bytes(kind.encode("ascii"))
        self._add_bytes(b"1" if executable else b"0")
        self._add_bytes(payload)

    def _add_bytes(self, value: bytes) -> None:
        self._hash.update(len(value).to_bytes(8, "big"))
        self._hash.update(value)

    def hexdigest(self) -> str:
        return self._hash.hexdigest()


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"corpus manifest does not exist or is not a file: {path}")
    try:
        with path.open("rb") as handle:
            manifest = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read corpus manifest {path}: {exc}") from exc

    expected = {"schema_version", "id", "version", "visibility"}
    missing = sorted(expected - manifest.keys())
    unknown = sorted(manifest.keys() - expected)
    if missing:
        raise ValueError(f"corpus manifest is missing fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"corpus manifest has unknown fields: {', '.join(unknown)}")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("corpus schema_version must be 1")
    corpus_id = manifest["id"]
    if not isinstance(corpus_id, str) or CORPUS_ID_PATTERN.fullmatch(corpus_id) is None:
        raise ValueError("corpus id must be a lowercase hyphenated slug")
    version = manifest["version"]
    if not isinstance(version, str) or not version.strip():
        raise ValueError("corpus version must be a non-empty string")
    visibility = manifest["visibility"]
    if not isinstance(visibility, str) or visibility not in VALID_VISIBILITIES:
        choices = ", ".join(sorted(VALID_VISIBILITIES))
        raise ValueError(f"corpus visibility must be one of: {choices}")
    return manifest


def _task_entries(
    task: Task, corpus_root: Path
) -> Iterable[tuple[str, str, bool, bytes]]:
    task_prefix = task.root.relative_to(corpus_root)
    for name in ("metadata.toml", "prompt.md"):
        yield _path_entry(task.root / name, corpus_root, task_prefix / name)
    for name in ("starter", "reference", "tests"):
        yield from _tree_entries(
            task.root / name, corpus_root, prefix=task_prefix / name
        )


def _tree_entries(
    root: Path, corpus_root: Path, *, prefix: Path
) -> Iterable[tuple[str, str, bool, bytes]]:
    if root.is_symlink():
        yield _path_entry(root, corpus_root, prefix)
        return
    resolved_root = _require_directory_root(root, corpus_root, "corpus content root")
    yield from _walk_directory(resolved_root, corpus_root, prefix)


def _walk_directory(
    directory: Path, corpus_root: Path, prefix: Path
) -> Iterable[tuple[str, str, bool, bytes]]:
    try:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
    except OSError as exc:
        raise ValueError(f"cannot inspect corpus directory {directory}: {exc}") from exc
    for entry in entries:
        path = Path(entry.path)
        relative = prefix / entry.name
        try:
            metadata = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise ValueError(f"cannot inspect corpus path {path}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode) or stat.S_ISREG(metadata.st_mode):
            yield _path_entry(path, corpus_root, relative)
        elif stat.S_ISDIR(metadata.st_mode):
            resolved = path.resolve()
            _require_within(resolved, corpus_root, f"directory {path}")
            yield from _walk_directory(resolved, corpus_root, relative)
        else:
            raise ValueError(f"unsupported corpus file kind: {path}")


def _path_entry(
    path: Path, corpus_root: Path, relative: Path
) -> tuple[str, str, bool, bytes]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot inspect corpus path {path}: {exc}") from exc
    executable = bool(metadata.st_mode & 0o111)
    if stat.S_ISLNK(metadata.st_mode):
        target = os.readlink(path)
        resolved_target = (path.parent / target).resolve(strict=False)
        _require_within(resolved_target, corpus_root, f"symlink target for {path}")
        return relative.as_posix(), "symlink", executable, os.fsencode(target)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"unsupported corpus file kind: {path}")
    _require_within(path.resolve(), corpus_root, f"regular file {path}")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read corpus file {path}: {exc}") from exc
    return relative.as_posix(), "regular", executable, payload


def _require_within(path: Path, root: Path, label: str) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes corpus root {root}: {path}") from exc


def _require_directory_root(path: Path, corpus_root: Path, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} does not exist or cannot be inspected: {path}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        target = path.resolve(strict=False)
        _require_within(target, corpus_root, f"{label} symlink target")
        raise ValueError(f"{label} must not be a symlink: {path}")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{label} is not a directory: {path}")
    resolved = path.resolve()
    _require_within(resolved, corpus_root, label)
    return resolved


def _require_regular_file(path: Path, corpus_root: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} does not exist or cannot be inspected: {path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"{label} must be a regular file: {path}")
    _require_within(path.resolve(), corpus_root, label)


def _reject_symlinked_task_roots(tasks_dir: Path) -> None:
    try:
        entries = sorted(os.scandir(tasks_dir), key=lambda entry: entry.name)
    except OSError as exc:
        raise ValueError(f"cannot inspect tasks directory {tasks_dir}: {exc}") from exc
    for entry in entries:
        if entry.is_symlink():
            raise ValueError(f"task root must not be a symlink: {entry.path}")
