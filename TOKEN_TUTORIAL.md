# MTAA Connect API Token Guide

This guide shows how to create a JWT access token and use it to authorize API requests.

## 1) Register a user (citizen)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Citizen",
    "email": "jane@example.com",
    "phone": "+255700000000",
    "gender": "female",
    "age": 25,
    "address": "Mikocheni B, Mwenge Road",
    "nida_number": "",
    "password": "StrongPass123",
    "confirm_password": "StrongPass123"
  }'
```

## 2) Login and get tokens

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@example.com",
    "password": "StrongPass123"
  }'
```

Response example:
```json
{
  "refresh": "REFRESH_TOKEN",
  "access": "ACCESS_TOKEN"
}
```

## 3) Use the access token

Add the token to the `Authorization` header:

```bash
curl -X GET http://127.0.0.1:8000/api/me/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## 4) Refresh the access token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "REFRESH_TOKEN"
  }'
```

Response example:
```json
{
  "access": "NEW_ACCESS_TOKEN"
}
```

## Officer login (role‑checked)

Only users with `role=officer` or `role=admin` can login here:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/officer-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "officer@example.com",
    "password": "StrongPass123"
  }'
```

## Use Swagger UI

1. Open `http://127.0.0.1:8000/docs/`
2. Click **Authorize**
3. Paste:

```
Bearer ACCESS_TOKEN
```

Then call protected endpoints.

## Notes

- Access tokens expire quickly; use the refresh token to get a new access token.
- For production, replace `127.0.0.1:8000` with your Render domain.
