"""T0.4: export Day 6 chunks (strategy A, B) from pgvector to Day 7 JSON (data/chunks_A.json, data/chunks_B.json)."""
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(".env")
Path("data").mkdir(exist_ok=True)
with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as conn:
    for s in ("A", "B"):
        rows = conn.execute("""SELECT chunk_id, document_id, source, page, text, metadata
                               FROM chunks WHERE strategy = %s ORDER BY chunk_id""", (s,)).fetchall()
        out = [{"id": cid, "text": t, "source_id": doc, "source": src, "page": p,
                "metadata": {**md, "strategy": s}} for cid, doc, src, p, t, md in rows]
        if not out:
            raise SystemExit(f"strategy {s}: 0 chunk trong DB — kiểm tra Docker Day 6")
        Path(f"data/chunks_{s}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{s}: {len(out)} chunk -> data/chunks_{s}.json | metadata keys: {sorted(out[0]['metadata'])}")
