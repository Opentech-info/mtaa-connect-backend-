# Backend (Django)

## Setup
1. Create a virtual environment and install dependencies.
2. Create a MySQL database in XAMPP (e.g., `mtaa_connect`).
3. Create a `.env` file in this folder based on `.env.example`.
4. Run migrations, create a superuser, and start the server.

```sh
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Environment
See `.env.example` for required variables.

## Render Deployment
1. Push this backend folder as its own repo (so `manage.py` is at repo root).
2. On Render, create a Web Service from the repo.
3. Use `render.yaml` (Blueprint) or configure:
   - Build: `bash build.sh`
   - Start: `python manage.py migrate` then `python manage.py initadmin` then `gunicorn backend.wsgi:application`
4. Set env vars:
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY=...`
   - `DJANGO_ALLOWED_HOSTS=your-render-domain,mtaaconnect.azsubay.com`
   - `CORS_ALLOWED_ORIGINS=https://your-frontend-domain`
   - `CSRF_TRUSTED_ORIGINS=https://your-frontend-domain`
   - `DJANGO_SUPERUSER_EMAIL=admin@example.com`
   - `DJANGO_SUPERUSER_PASSWORD=strong-password`
   - `DJANGO_SUPERUSER_FULL_NAME=Admin User`
   - DB credentials for production
## API
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/me/`
- `GET, POST /api/requests/`
- `GET /api/requests/pending/`
- `POST /api/requests/<id>/approve/`
- `POST /api/requests/<id>/reject/`
- `GET /api/citizens/`
