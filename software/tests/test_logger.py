from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from rcj2027.logger import JsonlLogger


class LoggerTests(unittest.TestCase):
    def test_writes_jsonl_with_run_id_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs" / "run.jsonl"
            with JsonlLogger(path, "run-1") as logger:
                logger.log("start", mode="fake")
                logger.log("sensor", distance_mm=120, flags={"sonar_valid": True})

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)

            first = json.loads(lines[0])
            self.assertEqual(first["run_id"], "run-1")
            self.assertEqual(first["event"], "start")
            self.assertEqual(first["mode"], "fake")
            datetime.fromisoformat(first["ts"])

            second = json.loads(lines[1])
            self.assertEqual(second["distance_mm"], 120)
            self.assertTrue(second["flags"]["sonar_valid"])

    def test_bytes_are_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.jsonl"
            with JsonlLogger(path, "run-1") as logger:
                logger.log("tx", frame=b"V,1*4B\n")

            record = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["frame"], "V,1*4B\n")

    def test_reserved_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with JsonlLogger(Path(tmp) / "run.jsonl", "run-1") as logger:
                with self.assertRaises(ValueError):
                    logger.log("start", ts="x")
                with self.assertRaises(ValueError):
                    logger.log("start", run_id="altro")

    def test_empty_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                JsonlLogger(Path(tmp) / "run.jsonl", "")


if __name__ == "__main__":
    unittest.main()
