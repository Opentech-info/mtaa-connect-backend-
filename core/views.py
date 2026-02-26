from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


def health(request):
    return JsonResponse({"status": "ok"})


def home(request):
    base_url = request.build_absolute_uri("/")
    context = {
        "status": "Online",
        "api_health_url": f"{base_url}api/health/",
        "healthz_url": f"{base_url}healthz/",
        "api_docs_url": f"{base_url}docs/",
        "api_redoc_url": f"{base_url}redoc/",
        "admin_url": f"{base_url}admin/",
        "timestamp": timezone.now(),
    }
    return render(request, "core/home.html", context)


def api_root(request):
    base_url = request.build_absolute_uri("/")
    return JsonResponse(
        {
            "health": f"{base_url}api/health/",
            "healthz": f"{base_url}healthz/",
            "auth_register": f"{base_url}api/auth/register/",
            "auth_login": f"{base_url}api/auth/login/",
            "auth_refresh": f"{base_url}api/auth/refresh/",
            "me": f"{base_url}api/me/",
            "requests": f"{base_url}api/requests/",
            "pending_requests": f"{base_url}api/requests/pending/",
            "docs": f"{base_url}docs/",
            "redoc": f"{base_url}redoc/",
        }
    )
