import logging
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Module-level state with thread safety
_model = None
_model_failed = False
_model_lock = threading.Lock()
_model_name = "all-MiniLM-L6-v2"


def _load_model():
    """
    Loads the SentenceTransformer model exactly once.
    Thread-safe via a module-level lock.
    """
    global _model, _model_failed
    with _model_lock:
        if _model is not None or _model_failed:
            return
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading sentence-transformers model: {_model_name} ...")
            _model = SentenceTransformer(_model_name)
            # Warm up: encode a single string to trigger any lazy initialisation
            _model.encode("warmup", convert_to_numpy=True, normalize_embeddings=True)
            logger.info("SentenceTransformer loaded and warmed up successfully.")
        except Exception as exc:
            logger.warning(
                f"sentence-transformers unavailable or failed to load: {exc}. "
                "Falling back to lightweight hash embedder."
            )
            _model_failed = True


def get_sentence_transformer():
    """
    Returns the loaded SentenceTransformer model, or None if unavailable.
    Triggers a load on the first call.
    """
    if _model is None and not _model_failed:
        _load_model()
    return _model


# Keep the private alias so health.py can import it without changes
_get_sentence_transformer = get_sentence_transformer


def _lightweight_hash_embedding(text: str, dimension: int = 384) -> np.ndarray:
    """
    Deterministic feature-hashing fallback embedding.
    Extracts unigrams and character 3-grams into a normalized vector space.
    Provides reasonable lexical similarity without any ML dependencies.
    """
    vec = np.zeros(dimension, dtype=np.float32)
    words = text.lower().split()
    for word in words:
        h = hash(word) % dimension
        vec[h] += 1.0
        if len(word) >= 3:
            for i in range(len(word) - 2):
                ngram = word[i : i + 3]
                nh = hash(ngram) % dimension
                vec[nh] += 0.5

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


class EmbedderService:
    """
    Encodes text into fixed-size normalised float32 vectors.

    Strategy:
    1. If sentence-transformers loads successfully, use all-MiniLM-L6-v2
       (384-dim, trained on 1B+ sentence pairs — high-quality semantic similarity).
    2. Otherwise fall back to the lightweight hash-based embedder so the
       gateway remains fully functional without heavy ML dependencies.
    """

    DIMENSION = 384

    def __init__(self):
        # Kick off model loading in a background thread so the first HTTP
        # request is not blocked by the ~2 s model-load time.
        t = threading.Thread(target=_load_model, daemon=True, name="embedder-init")
        t.start()

    @property
    def model_name(self) -> str:
        return _model_name if _model is not None else "hash-fallback"

    @property
    def using_ml_model(self) -> bool:
        return _model is not None

    def embed_text(self, text: str) -> np.ndarray:
        """
        Converts *text* into a normalised 1-D float32 vector of length 384.
        Records latency and backend label to Prometheus.
        """
        import time  # local import to avoid circular import at module level

        model = get_sentence_transformer()
        t0 = time.time()

        if model is not None:
            try:
                emb = model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                self._record_embed_metrics("sentence_transformers", t0)
                return emb.astype(np.float32)
            except Exception as exc:
                logger.error(f"SentenceTransformer encode failed: {exc}. Using fallback.")

        result = _lightweight_hash_embedding(text, self.DIMENSION)
        self._record_embed_metrics("hash_fallback", t0)
        return result

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Batch-encode a list of texts. Uses the ML model's native batching when
        available for much better throughput than calling embed_text in a loop.
        """
        import time  # local import to avoid circular import at module level

        model = get_sentence_transformer()
        t0 = time.time()

        if model is not None:
            try:
                embeddings = model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=32,
                )
                self._record_embed_metrics("sentence_transformers", t0)
                return [e.astype(np.float32) for e in embeddings]
            except Exception as exc:
                logger.error(f"SentenceTransformer batch encode failed: {exc}. Using fallback.")

        results = [_lightweight_hash_embedding(t, self.DIMENSION) for t in texts]
        self._record_embed_metrics("hash_fallback", t0)
        return results

    @staticmethod
    def _record_embed_metrics(backend: str, t0: float) -> None:
        """Record embed latency and request count to Prometheus (best-effort)."""
        import time  # local import

        try:
            from app.services.metrics import EMBED_LATENCY_SECONDS, EMBED_REQUESTS_TOTAL  # noqa: PLC0415
            EMBED_LATENCY_SECONDS.labels(backend=backend).observe(time.time() - t0)
            EMBED_REQUESTS_TOTAL.labels(backend=backend).inc()
        except Exception:
            pass  # never let metrics instrumentation crash the hot path

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Cosine similarity between two 1-D vectors.
        Both vectors are assumed to be normalised (unit norm), so this is
        simply the dot product. Explicit norms are used as a safety net.
        """
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = float(np.dot(v1, v2) / (norm1 * norm2))
        return max(-1.0, min(1.0, dot))


embedder_service = EmbedderService()
