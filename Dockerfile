# TODO: finish me, this is a placeholder. I don't yet know the operational shape
# of a langgraph app in terms of possible mounts and secrets, likely lots of
# injected client tokens or ways to abstract these.


################################# BUILDER #########################################
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory and prevent Python from writing bytecode
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# TODO: copy only project artifacts.
COPY . .

# Cache and install dependencies first (improves rebuild speeds)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the source code and install the project
COPY src/ /app/src/
COPY pyproject.toml uv.lock README.md /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


################################### PROD ###########################################
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

# Run using the script defined in your pyproject.toml entry point
CMD ["agentic"]
