# Multimodal RAG Chatbot (AWS Bedrock + Textract + OpenSearch) — Enhanced & Commented

This repository mirrors the structure of `adris-misra/multimodal-rag-chatbot` and adds **comprehensive comments**,
**examples**, **tests**, **CI**, and a **Dockerfile** for an end‑to‑end, production‑ready reference.

## What’s new vs. baseline
- Rich **inline comments** and **docstrings** explaining *why* and *how*
- **Examples** embedded in code blocks where helpful
- **Unit tests** with sample JSON fixtures
- **GitHub Actions** workflow (lint + tests)
- **Dockerfile** for containerized runs

## Quickstart
```bash
pip install -r requirements.txt
export AWS_REGION=us-east-1
export S3_BUCKET=your-bucket
export S3_PREFIX=docs/
export OPENSEARCH_HOST=your-os-host
export OPENSEARCH_PORT=443
export OPENSEARCH_INDEX_TEXT=text-index
export OPENSEARCH_INDEX_TABLE=table-index
export OPENSEARCH_INDEX_IMAGE=image-index
export OPENSEARCH_SIGV4=true
export BEDROCK_EMBED_MODEL=amazon.titan-embed-text-v2
export BEDROCK_CLAUDE_MODEL=anthropic.claude-3-sonnet-20240229-v1:0

python ingest.py
python query.py "Show me Q1 sales in table format"
```
