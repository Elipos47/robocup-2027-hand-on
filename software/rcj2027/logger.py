"""Logger strutturato JSONL con run_id."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("ascii", errors="replace")
    if is_dataclass(value):
        return asdict(value)
    return str(value)


class JsonlLogger:
    """Scrive un record JSON per riga, con timestamp UTC e run_id."""

    def __init__(self, path: str | Path, run_id: str) -> None:
        if not run_id:
            raise ValueError("run_id non puo' essere vuoto")

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self._file = self.path.open("a", encoding="utf-8")

    def log(self, event: str, **fields: Any) -> None:
        if not event:
            raise ValueError("event non puo' essere vuoto")
        if "event" in fields or "ts" in fields or "run_id" in fields:
            raise ValueError("campo riservato nel log")

        record: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "run_id": self.run_id,
            "event": event,
        }
        record.update(fields)

        self._file.write(
            json.dumps(record, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n"
        )
        self._file.flush()

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> "JsonlLogger":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
