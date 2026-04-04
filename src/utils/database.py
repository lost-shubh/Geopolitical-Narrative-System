"""
Lightweight SQLite persistence for pipeline runs.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class PipelineDatabase:
    """Store stage results for debugging and auditability."""

    def __init__(self, db_path: str = "data/processed/pipeline_results/pipeline_runs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def record_stage(self, run_id: str, stage: str, status: str, payload: Optional[Dict[str, Any]] = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pipeline_runs (run_id, stage, status, payload)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, stage, status, json.dumps(payload or {}, ensure_ascii=False)),
            )
            connection.commit()

    def latest_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT run_id, stage, status, payload, created_at
                FROM pipeline_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "run_id": row[0],
                "stage": row[1],
                "status": row[2],
                "payload": json.loads(row[3] or "{}"),
                "created_at": row[4],
            }
            for row in rows
        ]
