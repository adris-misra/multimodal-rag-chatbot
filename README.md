# Multimodal RAG Chatbot (AWS Bedrock + Textract + OpenSearch)

This repository contains a **production-ready multimodal Retrieval-Augmented Generation (RAG) chatbot** built on AWS.
It retrieves answers not only from text but also from **tables and images** embedded in documents.

## 🚀 Features
- Ingest PDFs from S3 using **Amazon Textract**
- Extract **text, tables, and figures with captions**
- Generate embeddings with **Amazon Titan Embeddings** via Bedrock
- Store in **Amazon OpenSearch Service** (vector index)
- Query pipeline retrieves text, tables, and images in parallel
- Fuse results and build context for **Claude 3 Sonnet (Bedrock)**
- End-to-end working code with modular design

## 📁 Folder Structure
```
multimodal-rag/
├── config.py
├── embeddings.py
├── vector_store.py
├── ingest.py
├── query.py
├── utils/
│   ├── textract_parser.py
│   ├── chunk_joiner.py
│   └── caption_extractor.py
└── prompt_templates/
    └── claude_prompt.txt
```

## ⚙️ Setup

1) Install dependencies:
```bash
pip install -r requirements.txt
```

2) Export environment variables (example):
```bash
export AWS_REGION=us-east-1
export S3_BUCKET=your-bucket
export S3_PREFIX=docs/
export OPENSEARCH_HOST=your-opensearch-hostname
export OPENSEARCH_PORT=443
export OPENSEARCH_INDEX_TEXT=text-index
export OPENSEARCH_INDEX_TABLE=table-index
export OPENSEARCH_INDEX_IMAGE=image-index
export OPENSEARCH_SIGV4=true
export BEDROCK_EMBED_MODEL=amazon.titan-embed-text-v2
export BEDROCK_CLAUDE_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

3) Ingest documents from S3:
```bash
python ingest.py
```

4) Ask questions:
```bash
python query.py "Show me Q1 sales in table format"
```

## 🔒 Notes
- For Amazon OpenSearch Serverless/managed, prefer **SigV4** auth (`OPENSEARCH_SIGV4=true`).
- Ensure your role/user has permissions for S3, Textract, Bedrock, and OpenSearch.

## 📚 References
- [Amazon Textract Docs](https://docs.aws.amazon.com/textract/latest/dg/what-is.html)
- [AWS Bedrock Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [OpenSearch Vector Search](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/vector-search.html)
