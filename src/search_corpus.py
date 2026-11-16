"""T0.6: keyword search over the OCR text of pages 1-32 (the indexed corpus) to prove a question has no evidence.

Usage: python -m src.search_corpus "phạt" "xử phạt" "mức phạt"
Case-insensitive, whitespace collapsed. Prints every hit with its page and surrounding text.
"""
import json
import sys
from pathlib import Path

PAGES = Path("../../Day6/K5-L3B-Day06-DataIngestionEngineering/starter/results/pages_TT-91-2026.jsonl")
FIRST, LAST = 1, 32  # indexed range (Day 6 manifest)


def load_pages():
    pages = [json.loads(l) for l in PAGES.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {p["page"]: " ".join(p["text"].split()) for p in pages if FIRST <= p["page"] <= LAST}


def search(pages, kw, width=70):
    kw_l, out = kw.lower(), []
    for page, text in pages.items():
        low, i = text.lower(), 0
        while (i := low.find(kw_l, i)) >= 0:
            out.append((page, text[max(0, i - width):i + len(kw) + width]))
            i += len(kw_l)
    return out


if __name__ == "__main__":
    pages = load_pages()
    for kw in sys.argv[1:]:
        hits = search(pages, kw)
        print(f"=== '{kw}': {len(hits)} kết quả")
        for page, snip in hits:
            print(f"  p{page}: ...{snip}...")
