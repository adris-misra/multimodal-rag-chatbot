"""
vector_store.py
Abstraction around Amazon OpenSearch for vector storage & KNN retrieval.

Responsibilities:
  • Connect to OpenSearch (SigV4 or Basic auth)
  • Ensure indexes exist with `knn_vector` mapping
  • Upsert documents into modality-specific indexes
  • Perform KNN vector search for retrieval

Example document stored in OpenSearch:
{
  "content": "| Region | Sales |\n| --- | --- |\n| US | 5000 |",
  "embedding": [0.12, -0.98, ...],
  "modality": "table",
  "metadata": {"source": "s3://.../file.pdf", "page": 2, "caption": "Quarterly sales results"}
}
"""
from __future__ import annotations
from typing import Any, Dict, List
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from config import Config

class VectorStore:
    """High-level helper around an OpenSearch client for vector search."""

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or Config()
        self.client = self._connect()
        # Ensure that all indexes exist (idempotent)
        self._ensure_index(self.cfg.index_text)
        self._ensure_index(self.cfg.index_table)
        self._ensure_index(self.cfg.index_image)

    def _connect(self) -> OpenSearch:
        """Connect to OpenSearch with either Basic auth or AWS SigV4."""
        if self.cfg.os_sigv4:
            session = boto3.Session()
            credentials = session.get_credentials()
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.cfg.region,
                'aoss',  # service for OpenSearch Serverless
                session_token=credentials.token
            )
            return OpenSearch(
                hosts=[{"host": self.cfg.os_host, "port": self.cfg.os_port}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )
        else:
            # Basic auth (use only for self-managed or private clusters)
            auth = (self.cfg.os_user, self.cfg.os_pass) if self.cfg.os_user else None
            return OpenSearch(
                hosts=[{"host": self.cfg.os_host, "port": self.cfg.os_port}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=False,  # set True if certs are available
                connection_class=RequestsHttpConnection,
            )

    def _ensure_index(self, name: str) -> None:
        """Create an index with `knn_vector` mapping if it doesn't exist."""
        if self.client.indices.exists(index=name):
            return

        # Titan v2 vector length is 1536; update if you switch models.
        mapping = {
            "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
            "mappings": {
                "properties": {
                    "content":   {"type": "text"},
                    "modality":  {"type": "keyword"},
                    "metadata":  {"type": "object", "enabled": True},
                    "embedding": {"type": "knn_vector", "dimension": 1536},
                }
            }
        }
        self.client.indices.create(index=name, body=mapping)

    def upsert(self,
               index: str,
               doc_id: str,
               content: str,
               embedding: List[float],
               modality: str,
               metadata: Dict[str, Any]) -> None:
        """Insert or update a document with its vector and metadata."""
        body = {
            "content": content,
            "embedding": embedding,
            "modality": modality,
            "metadata": metadata,
        }
        self.client.index(index=index, id=doc_id, body=body, refresh=True)

    def knn(self, index: str, vector: List[float], k: int = 5) -> list[dict]:
        """Return top‑k nearest neighbors using OpenSearch KNN query."""
        q = {"size": k, "query": {"knn": {"embedding": {"vector": vector, "k": k}}}}
        res = self.client.search(index=index, body=q)
        return [hit for hit in res.get("hits", {}).get("hits", [])]
