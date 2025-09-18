"""
embeddings.py
Wrapper for Amazon Bedrock's Titan Embeddings model.
This module exposes a single function: `embed_text(text)`.
"""
from __future__ import annotations
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from config import Config

_bedrock = None

def _client():
    """Return a cached Bedrock runtime client (avoid re-creating per call)."""
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime", region_name=Config().region)
    return _bedrock

def embed_text(text: str, model_id: str | None = None) -> list[float]:
    """
    Generate an embedding vector for the given text using Titan.

    Args:
        text: Input text (empty text returns an empty vector)
        model_id: Optional override; defaults to Config().bedrock_embed_model

    Returns:
        A list[float] embedding vector. Titan v2 length is typically 1536.

    Example:
        >>> embed_text("Hello world")[:5]
        [0.0123, -0.0456, ...]
    """
    if not text:
        return []

    model_id = model_id or Config().bedrock_embed_model
    body = json.dumps({"inputText": text})

    try:
        # Call Bedrock embeddings
        resp = _client().invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(resp["body"].read())

        # Titan sometimes uses `embedding` or `vector` keys depending on version
        vec = payload.get("embedding") or payload.get("vector")
        if not isinstance(vec, list):
            raise ValueError(f"Unexpected embedding payload: {payload}")
        return vec

    except (BotoCoreError, ClientError, ValueError) as e:
        raise RuntimeError(f"Bedrock embedding failed: {e}")
