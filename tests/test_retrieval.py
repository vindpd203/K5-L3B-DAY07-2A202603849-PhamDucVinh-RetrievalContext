"""BM25, filter and RRF logic on a toy corpus (no DB, no model)."""
import unittest

from src import retrieval
from src.retrieval import BM25Retriever, HybridRetriever

CHUNKS = [
    {"id": "c1", "text": "Ký hiệu hóa đơn điện tử là nhóm sáu ký tự", "source_id": "d", "source": "s", "page": 4,
     "metadata": {"chapter": "II"}},
    {"id": "c2", "text": "Chứng từ điện tử khấu trừ thuế", "source_id": "d", "source": "s", "page": 29,
     "metadata": {"chapter": "III"}},
    {"id": "c3", "text": "Hiệu lực thi hành kể từ ngày 01 tháng 7", "source_id": "d", "source": "s", "page": 32,
     "metadata": {"chapter": "V"}},
]


class Fixed:
    def __init__(self, name, ids):
        self.name, self.ids = name, ids

    def search(self, query, *, filters=None, top_k=3):
        by_id = {c["id"]: c for c in CHUNKS}
        return [{**by_id[i], "score": 0, "rank": n + 1, "method": self.name} for n, i in enumerate(self.ids[:top_k])]


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self._orig = retrieval.load_chunks
        retrieval.load_chunks = lambda s: CHUNKS

    def tearDown(self):
        retrieval.load_chunks = self._orig

    def test_bm25_ranks_matching_chunk_first_and_ranks_are_1_based(self):
        res = BM25Retriever("A").search("ký hiệu hóa đơn gồm mấy ký tự", top_k=3)
        self.assertEqual(res[0]["id"], "c1")
        self.assertEqual([r["rank"] for r in res], list(range(1, len(res) + 1)))

    def test_bm25_filter_and_no_zero_score_results(self):
        self.assertEqual(BM25Retriever("A").search("điện tử", filters={"chapter": "III"}, top_k=3)[0]["id"], "c2")
        self.assertEqual(BM25Retriever("A").search("xyz không có", top_k=3), [])

    def test_rrf_prefers_chunk_ranked_well_by_both(self):
        h = HybridRetriever(Fixed("a", ["c1", "c2", "c3"]), Fixed("b", ["c2", "c3", "c1"]), k=60)
        self.assertEqual(h.search("q", top_k=3)[0]["id"], "c2")  # ranks 2+1 beat 1+3 and 3+2


if __name__ == "__main__":
    unittest.main()
