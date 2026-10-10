import json
from pathlib import Path
import unittest

from app.task_spec import TaskSpecification, canonical_task_json, task_digest
from openclaw_core_reference import GateError, parse_task_spec


VECTOR_PATH = Path(__file__).parent / "vectors" / "openclaw_task_spec.json"


class OpenClawTaskCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))

    def test_valid_shared_vectors_match_both_implementations_and_fixed_digests(self):
        for vector in self.vectors["valid"]:
            with self.subTest(input=vector["input"]):
                core_spec = parse_task_spec(vector["input"])
                watchtower_spec = TaskSpecification.model_validate(vector["input"])

                self.assertEqual(core_spec.as_dict(), vector["task_spec"])
                self.assertEqual(watchtower_spec.model_dump(mode="json"), vector["task_spec"])
                self.assertEqual(core_spec.canonical_json(), vector["canonical_json"])
                self.assertEqual(canonical_task_json(watchtower_spec), vector["canonical_json"])
                self.assertEqual(core_spec.digest(), vector["sha256"])
                self.assertEqual(task_digest(canonical_task_json(watchtower_spec)), vector["sha256"])

    def test_invalid_shared_vectors_are_rejected_by_both_implementations(self):
        for specification in self.vectors["invalid"]:
            with self.subTest(specification=specification):
                with self.assertRaises(GateError):
                    parse_task_spec(specification)
                with self.assertRaises(ValueError):
                    TaskSpecification.model_validate(specification)

    def test_core_and_watchtower_normalize_url_inputs_identically(self):
        for vector in self.vectors["valid"]:
            with self.subTest(url=vector["input"]["url"]):
                core_url = parse_task_spec(vector["input"]).url
                watchtower_url = TaskSpecification.model_validate(vector["input"]).url
                self.assertEqual(watchtower_url, core_url)


if __name__ == "__main__":
    unittest.main()
