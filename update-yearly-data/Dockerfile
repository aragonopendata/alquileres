FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install dependencies from lockfile (reproducible)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY update_yearly_data.py .

RUN mkdir -p /data

ENTRYPOINT ["uv", "run", "update_yearly_data.py"]
CMD ["2025"]
