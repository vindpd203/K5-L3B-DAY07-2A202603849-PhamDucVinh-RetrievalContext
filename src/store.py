"""Store and search vectors in PostgreSQL + pgvector (exact cosine search, no ANN index).

One table for all strategies; primary key (strategy, chunk_id) makes re-ingest idempotent.
Strategy C reuses the strategy-B rows and only adds a metadata filter at query time.
"""
import json
from typing import Any

import psycopg

from .models import Chunk

FILTERABLE = {"chapter", "article", "document_id"}  # only these keys may reach the WHERE clause


def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.database_url = database_url
        self.dimensions = dimensions

    def _connect(self):
        return psycopg.connect(self.database_url, connect_timeout=5)

    def create_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    strategy    text    NOT NULL,
                    chunk_id    text    NOT NULL,
                    document_id text    NOT NULL,
                    source      text    NOT NULL,
                    page        integer NOT NULL,
                    pages       integer[] NOT NULL,
                    chapter     text,
                    article     integer,
                    text        text    NOT NULL,
                    metadata    jsonb   NOT NULL,
                    embedding   vector({self.dimensions}) NOT NULL,
                    PRIMARY KEY (strategy, chunk_id)
                )""")
            dim = conn.execute("""SELECT atttypmod FROM pg_attribute
                                  WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'""").fetchone()[0]
            if dim != self.dimensions:
                raise RuntimeError(f"table chunks has vector({dim}) but model gives {self.dimensions}; "
                                   "drop the table or use another database")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> dict[str, int]:
        """Insert/update by (strategy, chunk_id); delete this strategy's obsolete chunks of the same documents."""
        if len(chunks) != len(vectors):
            raise ValueError(f"{len(chunks)} chunks but {len(vectors)} vectors")
        if any(len(v) != self.dimensions for v in vectors):
            raise ValueError(f"vector dimension differs from {self.dimensions}")
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("duplicate chunk_id in batch")
        rows = [(strategy, c.chunk_id, c.document_id, c.source, c.page, c.metadata.get("pages", [c.page]),
                 c.metadata.get("chapter"), c.metadata.get("article"), c.text,
                 json.dumps(c.metadata, ensure_ascii=False), _vec(v)) for c, v in zip(chunks, vectors)]
        with self._connect() as conn, conn.cursor() as cur:  # one transaction
            cur.executemany("""
                INSERT INTO chunks (strategy, chunk_id, document_id, source, page, pages, chapter, article,
                                    text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)
                ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                    document_id = EXCLUDED.document_id, source = EXCLUDED.source, page = EXCLUDED.page,
                    pages = EXCLUDED.pages, chapter = EXCLUDED.chapter, article = EXCLUDED.article,
                    text = EXCLUDED.text, metadata = EXCLUDED.metadata, embedding = EXCLUDED.embedding""", rows)
            cur.execute("""DELETE FROM chunks WHERE strategy = %s AND document_id = ANY(%s)
                           AND NOT (chunk_id = ANY(%s))""",
                        (strategy, sorted({c.document_id for c in chunks}), [c.chunk_id for c in chunks]))
            deleted = cur.rowcount
        return {"upserted": len(rows), "deleted_obsolete": deleted}

    def count(self, strategy: str) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT count(*) FROM chunks WHERE strategy = %s", (strategy,)).fetchone()[0]

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Exact cosine search; score = 1 - cosine distance. Filter values are SQL parameters."""
        filters = filters or {}
        unknown = set(filters) - FILTERABLE
        if unknown:
            raise ValueError(f"filter keys not allowed: {sorted(unknown)}")
        keys = sorted(filters)
        where = " AND ".join(["strategy = %s"] + [f"{k} = %s" for k in keys])
        params = [strategy] + [filters[k] for k in keys]
        sql = f"""SELECT chunk_id, document_id, source, page, pages, chapter, article, text, metadata,
                         1 - (embedding <=> %s::vector) AS score
                  FROM chunks WHERE {where}
                  ORDER BY embedding <=> %s::vector LIMIT %s"""
        qv = _vec(query_vector)
        with self._connect() as conn, conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql, [qv] + params + [qv, top_k])
            return [dict(r, score=float(r["score"])) for r in cur.fetchall()]
