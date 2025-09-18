"""
config.py
Centralized configuration for AWS, OpenSearch, and Bedrock models.
All values are read from environment variables so the same code can run locally,
in Docker, or inside AWS Lambda.
"""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # --- AWS Region ---
    region: str = os.getenv("AWS_REGION", "us-east-1")

    # --- S3 (ingestion source) ---
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_prefix: str = os.getenv("S3_PREFIX", "")

    # --- OpenSearch (vector DB) ---
    os_host: str = os.getenv("OPENSEARCH_HOST", "localhost")
    os_port: int = int(os.getenv("OPENSEARCH_PORT", "443"))
    index_text: str = os.getenv("OPENSEARCH_INDEX_TEXT", "text-index")
    index_table: str = os.getenv("OPENSEARCH_INDEX_TABLE", "table-index")
    index_image: str = os.getenv("OPENSEARCH_INDEX_IMAGE", "image-index")

    # Auth mode: either Basic (user/pass) or SigV4 (for AOSS/managed)
    os_user: str | None = os.getenv("OPENSEARCH_BASIC_USER")
    os_pass: str | None = os.getenv("OPENSEARCH_BASIC_PASS")
    os_sigv4: bool = os.getenv("OPENSEARCH_SIGV4", "false").lower() == "true"

    # --- Bedrock models ---
    bedrock_embed_model: str = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2")
    bedrock_claude_model: str = os.getenv("BEDROCK_CLAUDE_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
