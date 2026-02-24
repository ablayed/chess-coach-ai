"""Verify the sentence-transformers embedding model loads and encodes text."""

from __future__ import annotations

import time

from sentence_transformers import SentenceTransformer


def main() -> None:
    print("Loading embedding model...")
    start = time.time()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"Model loaded in {time.time() - start:.1f}s")

    test_text = "controlling the center with pawns in the opening"
    embedding = model.encode(test_text)
    print(f"Embedding shape: {embedding.shape}")
    print(f"First 5 values: {embedding[:5]}")
    print("Embedding model works!")


if __name__ == "__main__":
    main()
