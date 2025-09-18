# Minimal Dockerfile for local testing of the query pipeline
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV AWS_REGION=us-east-1
CMD ["python", "query.py", "What tables are in this document?"]
