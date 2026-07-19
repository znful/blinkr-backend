# Blinkr

A URL shortener REST API built with Django and Django REST Framework.

## Features

- Shorten URLs with auto-generated or custom slugs
- Redirect with a 302 to the original URL
- Click tracking: device type, browser, OS, referrer domain, UTM parameters
- Per-link controls: expiry date, max click limit, active/inactive toggle
- Soft delete — links are never hard-removed by default
- Async click recording via Celery
- Password-protected links *(coming soon)*

## Stack

- Python 3.13
- Django 6 + Django REST Framework
- PostgreSQL (SQLite for zero-config local dev)
- Celery + Redis for async click recording
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) for JWT auth
- [uv](https://docs.astral.sh/uv/) for dependency management
- [user-agents](https://github.com/selwin/python-user-agents) for UA parsing

## Getting started

### With Docker (recommended — runs Postgres, Redis, the app, and the Celery worker together)

**Prerequisites:** Docker, Docker Compose

```bash
git clone https://github.com/znful/blinkr-backend
cd blinkr-backend

docker compose up
```

The app is then available at `http://localhost:8000`. Source is bind-mounted, so edits are picked up without rebuilding. For a production-style run (baked-in code, gunicorn, non-root user), copy `.env.example` to `.env`, fill in real values, and run:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Without Docker

**Prerequisites:** Python 3.13, [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
git clone https://github.com/znful/blinkr-backend
cd blinkr-backend

uv sync
uv run manage.py migrate
uv run manage.py runserver
```

This uses SQLite and runs click recording eagerly only during tests — for real async recording you'll also need Redis running locally and a worker: `uv run celery -A blinkr worker -l info`.

## API

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register/` | Create an account |
| `POST` | `/api/v1/auth/login/` | Exchange username + password for an access/refresh token pair |
| `POST` | `/api/v1/auth/refresh/` | Exchange a refresh token for a new access token |
| `POST` | `/api/v1/auth/logout/` | Blacklist a refresh token, invalidating it |

**Register payload**

```json
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "correct-horse-battery-staple"
}
```

Passwords are checked against Django's configured password validators.

**Login payload**

```json
{
  "username": "jane",
  "password": "correct-horse-battery-staple"
}
```

Returns `{"access": "...", "refresh": "..."}`. Access tokens live 15 minutes; refresh tokens live 7 days. Authenticate other requests with `Authorization: Bearer <access>`.

`logout` requires a valid access token (`Authorization` header) and the refresh token to blacklist in the body: `{"refresh": "..."}`.

---

### Redirect

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/<slug>` | Redirect to the original URL |

Returns `302` on success. Returns `404` if the slug doesn't exist. Returns `410 Gone` if the link is inactive, expired, or has reached its click limit.

---

### Short URLs

All endpoints require authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/urls/` | List your short URLs |
| `POST` | `/api/v1/urls/` | Create a short URL |
| `GET` | `/api/v1/urls/{id}/` | Retrieve a short URL |
| `PATCH` | `/api/v1/urls/{id}/` | Update a short URL |
| `DELETE` | `/api/v1/urls/{id}/` | Soft-delete a short URL |

**Create payload**

```json
{
  "original_url": "https://example.com/some/long/path",
  "slug": "my-link",
  "expires_at": "2026-12-31T23:59:59Z",
  "max_clicks": 100
}
```

`slug`, `expires_at`, and `max_clicks` are optional. If `slug` is omitted, one is auto-generated.

## Running tests

```bash
uv run manage.py test
```

## Project structure

```
apps/core/
  models.py        # ShortURL, Click
  mixins.py        # TimestampsMixin, SoftDeleteMixin
  serializers.py   # ShortURLSerializer, RegisterSerializer
  tasks.py         # record_click (Celery task)
  views/
    v1.py          # ShortURLViewSet (CRUD API)
    redirect.py    # redirect_view (public redirect + click recording)
    auth.py        # RegisterView, LogoutView
  urls/
    v1.py          # API router
    auth.py        # register/login/logout/refresh routes
  utils/
    slugs.py       # Auto slug generation
    user_agent.py  # UA parsing (device, browser, OS)

blinkr/
  celery.py        # Celery app instance

docker/
  Dockerfile       # Multi-stage: dev (runserver, bind mount) / prod (gunicorn, non-root)
```
