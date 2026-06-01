# Deployment & Fixes Guide

This document summarizes the diagnostic findings, the code fixes required, and a step-by-step plan to prepare the project for local testing and production deployment.

---

## Overview

The app is a small Django project (`news` app) that fetches headlines from an external News API. Common issues found during inspection and testing:

- Hard-coded secrets in `core/settings.py` and misformatted `.env`.
- `DEBUG = True` and `ALLOWED_HOSTS` empty (unsafe for production).
- Blocking external API calls in `news/views.py` without timeout or caching (causes requests to hang).
- No `STATIC_ROOT` or production static handling (required for `DEBUG=False`).
- No `requirements.txt` or production process files (Gunicorn/systemd/Nginx).

---

## Diagnosed Failure Points (what caused the loading/stuck behavior)

- Blocking external HTTP call in the view: the call to the News API blocks the view thread when the remote API is slow/unavailable.
- `.env` formatting included extra quotes/spaces for `NEWS_API_KEY`, which can lead to invalid API keys.
- No timeout on external requests or caching means every user request hits the remote API synchronously.

---

## Code Fix Recommendations (concise)

- Fix `.env` formatting

```text
# .env (example)
NEWS_API_KEY=YOUR_NEWS_API_KEY
DJANGO_SECRET_KEY=replace-with-a-secure-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

- Read secrets and debug from environment in `core/settings.py` (example snippet)

```python
# core/settings.py (top)
from dotenv import load_dotenv
import os
from pathlib import Path
import dj_database_url

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1').split(',')

# Database (use DATABASE_URL if provided)
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'))
}
```

- Static files & Whitenoise (add near bottom of settings)

```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... rest of middleware ...
]
```

- Replace blocking view with timeout + cache + fallback (example for `news/views.py`)

```python
# news/views.py
from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache
import requests

CACHE_KEY = 'top_headlines_v1'
CACHE_TTL = 300  # seconds

def news_view(request):
    articles = cache.get(CACHE_KEY)
    if articles is None:
        try:
            resp = requests.get(
                'https://newsapi.org/v2/top-headlines',
                params={'country': 'us', 'language': 'en', 'category': 'business'},
                headers={'X-Api-Key': settings.NEWS_API_KEY},
                timeout=5,
            )
            resp.raise_for_status()
            articles = resp.json().get('articles', [])
            cache.set(CACHE_KEY, articles, CACHE_TTL)
        except Exception:
            articles = []
    return render(request, 'new_home.html', {'articles': articles})
```

- Add `requirements.txt` (minimal list)

```
Django==5.2.12
python-dotenv
newsapi-python
requests
whitenoise
gunicorn
dj-database-url
psycopg2-binary
```

---

## Step-by-step Plan (commands)

1. Create & activate a virtual environment

```bash
python3 -m venv env
source env/bin/activate
```

2. Install dependencies and freeze

```bash
pip install -r requirements.txt
# or if starting from scratch
pip install Django python-dotenv newsapi-python requests whitenoise gunicorn dj-database-url psycopg2-binary
pip freeze > requirements.txt
```

3. Fix `.env` (remove quotes/spaces) and set production env vars on the VPS

4. Update `core/settings.py` (apply snippets above)

5. Update `news/views.py` to use `requests` with `timeout` and caching

6. Run migrations and collectstatic

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

7. Local test

```bash
python manage.py runserver 0.0.0.0:8000
curl -v http://127.0.0.1:8000/
```

8. Prepare production process files (example: Gunicorn systemd unit + Nginx site) and configure `DJANGO_ALLOWED_HOSTS` on the server.

9. Enable HTTPS (Certbot) and start services

---

## Troubleshooting checklist

- If page loads but images/CSS missing: ensure `collectstatic` was run and static files are served from `STATIC_ROOT`.
- If server returns `Connection refused`: ensure `runserver` is running and listening (`ss -ltnp | grep :8000`).
- If page is stuck/loading: test News API from Django shell to measure latency.
- If ImportError/ModuleNotFoundError: install the missing package into the active venv.

---

## Quick recommended next steps (I can do these for you)

- I can generate the exact `core/settings.py` and `news/views.py` patches. Reply **Generate patches** to apply them.
- I can produce a `requirements.txt` file from your environment. Reply **Generate requirements**.

---

## Checklist

- [ ] Fix `.env`
- [ ] Update `core/settings.py`
- [ ] Update `news/views.py` (timeout + cache)
- [ ] Add static handling & run `collectstatic`
- [ ] Create `requirements.txt`
- [ ] Add production process configs (Gunicorn/systemd/Nginx)
- [ ] Harden security settings and enable HTTPS

---

End of document.
