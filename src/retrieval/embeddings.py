from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

# Keep the model cache with the project so a later run works offline once the
# required model has been downloaded. Respect an explicitly configured cache.
_project_dir = Path(__file__).resolve().parents[2]
os.environ.setdefault("HF_HOME", str(_project_dir / ".model-cache"))

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer:
    # SentenceTransformer may make a Hub metadata request even when every
    # model file is cached. Prefer the cached snapshot path when available.
    repo_cache = Path(os.environ["HF_HOME"]) / "hub" / f"models--{model_name.replace('/', '--')}"
    revision_file = repo_cache / "refs" / "main"
    if revision_file.exists():
        snapshot = repo_cache / "snapshots" / revision_file.read_text(encoding="utf-8").strip()
        if (snapshot / "modules.json").exists():
            model_name = str(snapshot)
    return SentenceTransformer(model_name)


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = _load_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()
