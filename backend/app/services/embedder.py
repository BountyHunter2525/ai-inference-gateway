import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

_model = None
_model_failed = False


def _get_sentence_transformer():
    global _model, _model_failed
    if _model is not None:
        return _model
    if _model_failed:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers/all-MiniLM-L6-v2...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer loaded successfully.")
        return _model
    except Exception as e:
        logger.warning(f"sentence-transformers not available or failed to load: {e}. Falling back to lightweight embedder.")
        _model_failed = True
        return None


def _lightweight_hash_embedding(text: str, dimension: int = 384) -> np.ndarray:
    """
    Lightweight, deterministic feature hashing fallback embedding.
    Extracts word and character 3-grams into normalized vector space.
    Provides semantic-like similarity for similar text without heavy PyTorch dependencies.
    """
    vec = np.zeros(dimension, dtype=np.float32)
    words = text.lower().split()
    for word in words:
        h = hash(word) % dimension
        vec[h] += 1.0
        # Character trigrams for morphological similarity
        if len(word) >= 3:
            for i in range(len(word) - 2):
                ngram = word[i:i+3]
                nh = hash(ngram) % dimension
                vec[nh] += 0.5
    
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


class EmbedderService:
    def __init__(self):
        self.dimension = 384

    def embed_text(self, text: str) -> np.ndarray:
        """
        Converts text into a normalized 1D float vector.
        """
        model = _get_sentence_transformer()
        if model is not None:
            try:
                emb = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return emb.astype(np.float32)
            except Exception as e:
                logger.error(f"Error in SentenceTransformer encode: {e}")
        
        return _lightweight_hash_embedding(text, self.dimension)

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Calculates cosine similarity between two 1D vectors: (v1 . v2) / (|v1| * |v2|).
        Since vectors are normalized, it is simply the dot product.
        """
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = float(np.dot(v1, v2) / (norm1 * norm2))
        # Clamp to [-1.0, 1.0] due to floating point nuances
        return max(-1.0, min(1.0, dot))


embedder_service = EmbedderService()
