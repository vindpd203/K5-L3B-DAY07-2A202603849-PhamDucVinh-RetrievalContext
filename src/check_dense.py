import os
from dotenv import load_dotenv
from src.embeddings import SentenceTransformerEmbedder
from src.store import PgVectorStore

load_dotenv(".env")
emb = SentenceTransformerEmbedder()
store = PgVectorStore(os.environ["DATABASE_URL"], emb.dimensions)
q = "Ký hiệu hóa đơn điện tử gồm bao nhiêu ký tự?"
for s in ("A", "B"):
    print("---", s, store.count(s), "chunks")
    for r in store.search(s, emb.embed_query(q), top_k=3):
        print(r["chunk_id"], "p", r["page"], round(r["score"], 3), r["text"][:70].replace("\n", " "))