from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from nixbench.corpus import identify_corpus
from tests.test_runner import make_toy_task


class CorpusIdentityTests(unittest.TestCase):
    def test_identity_is_stable_and_sorted_by_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root)
            make_named_toy_task(root / "tasks", "zeta")
            make_named_toy_task(root / "tasks", "alpha")

            first = identify_corpus(root / "tasks")
            second = identify_corpus(root / "tasks")

            self.assertEqual(first.digest, second.digest)
            self.assertEqual(first.task_ids, ("alpha", "zeta"))
            self.assertEqual(tuple(first.task_digests), first.task_ids)

    def test_task_content_and_executable_mode_change_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root)
            task = make_toy_task(root / "tasks")
            answer = task.reference_dir / "answer.txt"
            original = identify_corpus(root / "tasks")

            answer.write_text("changed\n")
            changed_content = identify_corpus(root / "tasks")
            self.assertNotEqual(original.digest, changed_content.digest)
            self.assertNotEqual(
                original.task_digests[task.id], changed_content.task_digests[task.id]
            )

            answer.write_text("reference\n")
            answer.chmod(answer.stat().st_mode | 0o100)
            changed_mode = identify_corpus(root / "tasks")
            self.assertNotEqual(original.digest, changed_mode.digest)

    def test_contract_content_changes_digest_but_site_content_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root)
            task = make_toy_task(root / "tasks")
            contract = root / "contracts" / task.id / "valid" / "case.toml"
            contract.parent.mkdir(parents=True)
            contract.write_text('outcome = "pass"\n')
            original = identify_corpus(root / "tasks")

            site_file = root / "site" / "index.html"
            site_file.parent.mkdir()
            site_file.write_text("site-only change")
            self.assertEqual(original.digest, identify_corpus(root / "tasks").digest)

            contract.write_text('outcome = "reject"\n')
            self.assertNotEqual(original.digest, identify_corpus(root / "tasks").digest)

    def test_external_non_git_corpus_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root, corpus_id="external-corpus")
            make_toy_task(root / "tasks")

            identity = identify_corpus(root / "tasks")

            self.assertEqual(identity.id, "external-corpus")
            self.assertEqual(identity.task_count, 1)

    def test_symlink_outside_corpus_is_rejected(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            tempfile.TemporaryDirectory() as outside,
        ):
            root = Path(temp)
            write_manifest(root)
            task = make_toy_task(root / "tasks")
            external = Path(outside) / "secret"
            external.write_text("secret")
            os.symlink(external, task.starter_dir / "escape")

            with self.assertRaisesRegex(
                ValueError, "symlink target.*escapes corpus root"
            ):
                identify_corpus(root / "tasks")

    def test_internal_symlink_descriptor_is_hashed_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root)
            task = make_toy_task(root / "tasks")
            os.symlink("answer.txt", task.starter_dir / "answer-link")

            identity = identify_corpus(root / "tasks")

            self.assertEqual(identity.task_count, 1)

    def test_nested_directory_symlink_outside_corpus_is_rejected(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            tempfile.TemporaryDirectory() as outside,
        ):
            root = Path(temp)
            write_manifest(root)
            task = make_toy_task(root / "tasks")
            external = Path(outside) / "directory"
            external.mkdir()
            (external / "secret").write_text("secret")
            os.symlink(external, task.starter_dir / "nested")

            with self.assertRaisesRegex(ValueError, "symlink target.*escapes"):
                identify_corpus(root / "tasks")

    def test_contracts_root_symlink_outside_corpus_is_rejected(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            tempfile.TemporaryDirectory() as outside,
        ):
            root = Path(temp)
            write_manifest(root)
            make_toy_task(root / "tasks")
            external = Path(outside) / "contracts"
            external.mkdir()
            os.symlink(external, root / "contracts")

            with self.assertRaisesRegex(ValueError, "contracts directory.*escapes"):
                identify_corpus(root / "tasks")

    def test_tasks_root_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_manifest(root)
            actual_tasks = root / "actual-tasks"
            make_toy_task(actual_tasks)
            os.symlink(actual_tasks, root / "tasks")

            with self.assertRaisesRegex(ValueError, "tasks directory must not be a symlink"):
                identify_corpus(root / "tasks")


def write_manifest(root: Path, *, corpus_id: str = "test-corpus") -> None:
    (root / "corpus.toml").write_text(
        "\n".join(
            [
                "schema_version = 1",
                f'id = "{corpus_id}"',
                'version = "1.0.0"',
                'visibility = "public"',
                "",
            ]
        )
    )


def make_named_toy_task(tasks_dir: Path, task_id: str) -> None:
    task = make_toy_task(tasks_dir)
    target = tasks_dir / task_id
    task.root.rename(target)
    metadata_path = target / "metadata.toml"
    metadata_path.write_text(
        metadata_path.read_text().replace('id = "toy"', f'id = "{task_id}"')
    )


if __name__ == "__main__":
    unittest.main()
