"""Phase 1 retrievers over one Day 6 chunk set (strategy "A" or "B").

All methods return the same shape, ranked best first:
    {"id", "text", "source_id", "source", "page", "metadata", "score", "rank", "method"}
Filters: only keys given by the user/question (e.g. {"chapter": "III"}); never derived from gold.

- DenseRetriever : Day 6 pgvector, exact cosine (score = cosine similarity).
- BM25Retriever  : Okapi BM25 over the exported chunks; Vietnamese tokenized as lowercase syllables,
                   optionally + syllable bigrams (approximates multi-syllable words like "hóa đơn").
- HybridRetriever: Reciprocal Rank Fusion of dense + BM25 candidate lists (rank-based, no score scaling).
"""
import json
import math
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv


def load_chunks(strategy):
    return json.loads(Path(f"data/chunks_{strategy}.json").read_text(encoding="utf-8"))


def _matches(chunk, filters):
    return all(chunk["metadata"].get(k) == v for k, v in (filters or {}).items())


def _ranked(items, method):
    """items: list of (chunk, score) best first -> result dicts."""
    return [{**c, "score": round(float(s), 6), "rank": i + 1, "method": method} for i, (c, s) in enumerate(items)]


class DenseRetriever:
    name = "dense"

    def __init__(self, strategy, embedder=None):
        from src.embeddings import SentenceTransformerEmbedder
        from src.store import PgVectorStore
        load_dotenv(".env")
        self.strategy = strategy
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.store = PgVectorStore(os.environ["DATABASE_URL"], self.embedder.dimensions)
        self.by_id = {c["id"]: c for c in load_chunks(strategy)}

    def search(self, query, *, filters=None, top_k=3):
        rows = self.store.search(self.strategy, self.embedder.embed_query(query), top_k=top_k, filters=filters)
        missing = [r["chunk_id"] for r in rows if r["chunk_id"] not in self.by_id]
        if missing:  # DB and exported JSON out of sync -> fail loudly, re-run src.export_chunks
            raise RuntimeError(f"chunks in DB but not in data/chunks_{self.strategy}.json: {missing[:3]}")
        return _ranked([(self.by_id[r["chunk_id"]], r["score"]) for r in rows], self.name)


def tokenize(text, bigrams=False):
    toks = re.findall(r"\w+", unicodedata.normalize("NFC", text).lower())
    return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])] if bigrams else toks


class BM25Retriever:
    def __init__(self, strategy, k1=1.5, b=0.75, bigrams=False):
        self.chunks = load_chunks(strategy)
        self.k1, self.b, self.bigrams = k1, b, bigrams
        self.name = "bm25" + ("+bigram" if bigrams else "")
        self.tf = [Counter(tokenize(c["text"], bigrams)) for c in self.chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avgdl = sum(self.len) / len(self.len)
        df = Counter(term for t in self.tf for term in t)
        n = len(self.chunks)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def search(self, query, *, filters=None, top_k=3):
        q = tokenize(query, self.bigrams)
        scored = []
        for c, tf, dl in zip(self.chunks, self.tf, self.len):
            if not _matches(c, filters):
                continue
            s = sum(self.idf.get(t, 0) * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
                    for t in q if t in tf)
            if s > 0:
                scored.append((c, s))
        scored.sort(key=lambda x: -x[1])
        return _ranked(scored[:top_k], self.name)


def _merge(a, b, max_overlap=80):
    """Join two consecutive chunk texts, dropping the overlap (strategy A windows overlap 36 chars)."""
    a, b = " ".join(a.split()), " ".join(b.split())
    k = next((k for k in range(min(max_overlap, len(a), len(b)), 0, -1) if a.endswith(b[:k])), 0)
    return a + " " + b[k:] if k == 0 else a + b[k:]


class Windows:
    """Expand a chunk to [prev, chunk, next] in chunk-id order. The window keeps the CENTER chunk id (a real id,
    so citations stay valid) with merged text and the union of pages. Used by retrieval and by evaluation."""

    def __init__(self, strategy, radius=1):
        self.chunks = sorted(load_chunks(strategy), key=lambda c: c["id"])
        self.pos = {c["id"]: i for i, c in enumerate(self.chunks)}
        self.radius = radius

    def get(self, chunk_id):
        i = self.pos[chunk_id]
        part = self.chunks[max(0, i - self.radius): i + self.radius + 1]
        text = part[0]["text"]
        for c in part[1:]:
            text = _merge(text, c["text"])
        center = self.chunks[i]
        pages = sorted({p for c in part for p in (c["metadata"].get("pages") or [c["page"]])})
        return {**center, "text": text, "metadata": {**center["metadata"], "pages": pages,
                                                      "window": [c["id"] for c in part]}}


def context_chunks(strategy, neighbors=0):
    """id -> the exact chunk/window text the model saw (for evaluation and manual review)."""
    if not neighbors:
        return {c["id"]: c for c in load_chunks(strategy)}
    w = Windows(strategy, neighbors)
    return {c["id"]: w.get(c["id"]) for c in w.chunks}


class NeighborRetriever:
    """Wrap any retriever: same ranking, each hit replaced by its neighbor window."""

    def __init__(self, inner, strategy, radius=1):
        self.inner, self.windows = inner, Windows(strategy, radius)
        self.name = f"{inner.name}+neighbors(±{radius})"

    def search(self, query, *, filters=None, top_k=3):
        # ponytail: overlapping windows of adjacent hits are kept as-is (some duplicated text in context)
        return [{**self.windows.get(r["id"]), "score": r["score"], "rank": r["rank"], "method": self.name}
                for r in self.inner.search(query, filters=filters, top_k=top_k)]


class HybridRetriever:
    def __init__(self, dense, lexical, k=60, candidates=20):
        self.dense, self.lexical, self.k, self.candidates = dense, lexical, k, candidates
        self.name = f"hybrid_rrf({dense.name}+{lexical.name},k={k},n={candidates})"

    def search(self, query, *, filters=None, top_k=3):
        fused, chunk = Counter(), {}
        for r in (self.dense, self.lexical):
            for hit in r.search(query, filters=filters, top_k=self.candidates):
                fused[hit["id"]] += 1 / (self.k + hit["rank"])
                chunk[hit["id"]] = {k: v for k, v in hit.items() if k not in ("score", "rank", "method")}
        return _ranked([(chunk[i], s) for i, s in fused.most_common(top_k)], self.name)
