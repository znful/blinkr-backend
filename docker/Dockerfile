# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

# Copy the uv binary straight from Astral's image instead of `pip install uv`
# — no need to bootstrap pip just to install the tool that replaces it.
COPY --from=ghcr.io/astral-sh/uv:0.9.13 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}"

# Dependencies only depend on these two files, so copying just them first
# means the (slow) `uv sync` layer is only invalidated when a dependency
# actually changes, not on every source edit.
COPY pyproject.toml uv.lock ./


# ---- dev ----
# Runs the dev server against source bind-mounted by docker-compose.yml,
# and keeps dev-only tools (ruff, mypy stubs, ty) installed.
FROM base AS dev

RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]


# ---- prod ----
# Bakes the source into the image (no bind mount), drops dev-only tools,
# runs as a non-root user, and serves via gunicorn instead of runserver.
FROM base AS prod

RUN uv sync --frozen --no-install-project --no-dev

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --chown=app:app . .
RUN uv sync --frozen --no-dev

# `uv run` normally re-syncs the environment against pyproject.toml/uv.lock
# on every invocation. In prod that's both wrong (it'd silently pull the
# "dev" group back in — ruff, mypy, ty) and impossible for a non-root user
# to do anyway (.venv is root-owned). Skip that check entirely and just run
# with whatever was baked into .venv above.
ENV UV_NO_SYNC=1

USER app

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "blinkr.wsgi:application", "--bind", "0.0.0.0:8000"]
