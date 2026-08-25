from __future__ import annotations

import base64
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .config import settings


def _archive_file_for_today() -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    return f"{settings.github_sync_path.rstrip('/')}/analyses-{day}.jsonl"


def _rows_for_today() -> list[dict]:
    db = Path(settings.data_dir) / "tradebot.db"
    if not db.exists():
        return []
    day_prefix = datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT a.*, o.status AS outcome_status, o.result AS outcome_result,
                   o.pnl_r AS outcome_pnl_r, o.exit_price, o.resolved_at,
                   o.max_favorable_r, o.max_adverse_r, o.tp1_hit
            FROM analysis_snapshots a
            LEFT JOIN outcome_tracking o ON o.analysis_id=a.id
            WHERE a.analyzed_at LIKE ?
            ORDER BY a.id ASC
            """,
            (day_prefix + "%",),
        ).fetchall()
    return [dict(row) for row in rows]


def sync_analysis_archive() -> dict[str, object]:
    """Upload today's analysis snapshots to GitHub using the configured PAT.

    The token must never be stored in source control. A GitHub token with
    Contents: write permission is required in GITHUB_SYNC_TOKEN.
    """
    token = settings.github_sync_token.strip()
    if not settings.github_sync_enabled:
        return {"enabled": False, "uploaded": False, "reason": "disabled"}
    if not token:
        return {"enabled": True, "uploaded": False, "reason": "GITHUB_SYNC_TOKEN missing"}

    rows = _rows_for_today()
    if not rows:
        return {"enabled": True, "uploaded": False, "reason": "no analyses for today", "count": 0}

    lines = "".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows)
    content_b64 = base64.b64encode(lines.encode("utf-8")).decode("ascii")
    path = _archive_file_for_today()
    url = f"https://api.github.com/repos/{settings.github_sync_repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    with httpx.Client(timeout=20.0, http2=True) as client:
        current = client.get(url, headers=headers, params={"ref": settings.github_sync_branch})
        sha = current.json().get("sha") if current.status_code == 200 else None
        payload = {
            "message": f"data: sync analysis archive {datetime.now(timezone.utc).date().isoformat()}",
            "content": content_b64,
            "branch": settings.github_sync_branch,
        }
        if sha:
            payload["sha"] = sha
        response = client.put(url, headers=headers, json=payload)
        response.raise_for_status()

    return {"enabled": True, "uploaded": True, "count": len(rows), "path": path}
