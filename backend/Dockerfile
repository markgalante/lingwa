FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt scripts/download_argos_model.py ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download nl_core_news_sm && \
    python download_argos_model.py

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
