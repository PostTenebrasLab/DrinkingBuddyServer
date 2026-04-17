FROM ghcr.io/astral-sh/uv:python3.14-alpine
WORKDIR /app
ENV UV_NO_DEV=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-workspace

COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable

EXPOSE 5000
ENV PATH="/app/.venv/bin:$PATH"
CMD ["ptl-buddy-server"]
