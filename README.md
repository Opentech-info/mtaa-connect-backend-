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
