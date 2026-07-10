from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CorpusPromptContractTests(unittest.TestCase):
    def test_prompts_document_evaluator_contract_details(self) -> None:
        required_phrases = {
            "flake-per-system-outputs": [
                "apps.${system}.default.meta.package",
            ],
            "lang-attrsets-normalize": [
                "Disabled packages still appear in `names` and `versions`",
                "exclude them only from `bySystem` and `defaultPackages`",
            ],
            "module-service-options": [
                "Do not assume additional `lib` helpers",
            ],
            "module-path-composition": [
                "Use parentheses around path additions inside lists",
                "Do not use `{moduleRoots.config}/...`",
            ],
            "package-python-application": [
                "lib.licenses.asl20",
            ],
            "purity-wrapper-derivation": [
                "Do not use `lib.getExe`",
            ],
        }

        missing = []
        for task_id, phrases in required_phrases.items():
            prompt = (REPO_ROOT / "tasks" / task_id / "prompt.md").read_text()
            for phrase in phrases:
                if phrase not in prompt:
                    missing.append(f"{task_id}: {phrase}")

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
