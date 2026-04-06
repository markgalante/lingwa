FROM python:3.11-slim

WORKDIR /app

# Set HOME to /app so argostranslate (and any other tool that writes to $HOME)
# uses a path that exists and will be owned by appuser after the chown below.
ENV HOME=/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/download_argos_model.py scripts/build_nl_dict.py ./
RUN python -m spacy download nl_core_news_sm && \
    python download_argos_model.py && \
    python build_nl_dict.py /app/data/nl_en_dict.json
    # Explicit path required: inside the image WORKDIR is /app, so the script's
    # default (relative to __file__) would resolve incorrectly. Locally, omit the
    # argument and the script defaults to backend/data/nl_en_dict.json.

COPY . .

RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
