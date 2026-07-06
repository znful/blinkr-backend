# Blinkr

A URL shortener REST API built with Django and Django REST Framework.

## Features

- Shorten URLs with auto-generated or custom slugs
- Redirect with a 302 to the original URL
- Click tracking: device type, browser, OS, referrer domain, UTM parameters
- Per-link controls: expiry date, max click limit, active/inactive toggle
- Soft delete — links are never hard-removed by default
- Password-protected links *(coming soon)*
- Async click recording via Celery *(coming soon)*

## Stack

- Python 3.13
- Django 6 + Django REST Framework
- [uv](https://docs.astral.sh/uv/) for dependency management
- [user-agents](https://github.com/selwin/python-user-agents) for UA parsing

## Getting started

**Prerequisites:** Python 3.13, [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
git clone https://github.com/znful/blinkr-backend
cd blinkr-backend

uv sync
uv run manage.py migrate
uv run manage.py runserver
```

## API

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
  serializers.py   # ShortURLSerializer
  views/
    v1.py          # ShortURLViewSet (CRUD API)
    redirect.py    # redirect_view (public redirect + click recording)
  urls/
    v1.py          # API router
  utils/
    slugs.py       # Auto slug generation
    user_agent.py  # UA parsing (device, browser, OS)
```
