FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md requirements.lock ./
COPY src ./src

FROM base AS app
RUN pip install --no-cache-dir -c requirements.lock '.[openai]' \
    && useradd --create-home --uid 10001 franark \
    && mkdir /app/data && chown franark:franark /app/data
USER franark
EXPOSE 8765
CMD ["uvicorn", "franark.app:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "1"]

FROM base AS docs
RUN pip install --no-cache-dir -c requirements.lock '.[docs]'
COPY docs ./docs
RUN python -m sphinx -W --keep-going -b html docs docs/_build/html
EXPOSE 8000
CMD ["python", "-m", "http.server", "8000", "--bind", "0.0.0.0", "--directory", "docs/_build/html"]
