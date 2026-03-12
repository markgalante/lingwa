FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download nl_core_news_sm && \
    python -m spacy download de_core_news_sm && \
    python -m spacy download fr_core_news_sm && \
    python -m spacy download es_core_news_sm

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
