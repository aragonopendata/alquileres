FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y  \
    gcc  \
    libpq-dev && \
      apt-get clean && \
      rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN pip install uv
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

COPY . /app

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/servicios/alquileres-api"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]