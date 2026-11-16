"""Local Sentence Transformers embedder (no API key, cost 0). Fails loudly; never falls back to mock vectors."""
from typing import Protocol

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class SentenceTransformerEmbedder:
    """Same model and normalization for documents and queries (this model uses no query/passage prefix).

    Vectors are L2-normalized, so cosine similarity = dot product.
    Note: the model truncates input beyond `max_seq_length` tokens (128 for this model);
    token_counts() lets the pipeline report how many chunks are truncated.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, batch_size: int = 32) -> None:
        from sentence_transformers import SentenceTransformer, __version__

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_embedding_dimension()
        self.max_seq_length = self.model.max_seq_length
        self.library_version = __version__
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 show_progress_bar=False)
        if len(vecs) != len(texts) or vecs.shape[1] != self.dimensions:
            raise RuntimeError(f"embedding shape {vecs.shape} does not match {len(texts)} x {self.dimensions}")
        return vecs.tolist()

    def embed_query(self, question: str) -> list[float]:
        return self.embed_documents([question])[0]

    def token_counts(self, texts: list[str]) -> list[int]:
        tok = self.model.tokenizer
        return [len(tok(t, add_special_tokens=True)["input_ids"]) for t in texts]
