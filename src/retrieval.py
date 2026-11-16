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
