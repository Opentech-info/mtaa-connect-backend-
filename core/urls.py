from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from . import api

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("health/", views.health, name="health"),
    path("auth/register/", api.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", api.MeView.as_view(), name="me"),
    path("requests/", api.CitizenRequestListCreate.as_view(), name="requests"),
    path("requests/pending/", api.PendingRequestList.as_view(), name="pending-requests"),
    path("requests/<int:pk>/", api.RequestDetail.as_view(), name="request-detail"),
    path("requests/<int:pk>/approve/", api.ApproveRequest.as_view(), name="request-approve"),
    path("requests/<int:pk>/reject/", api.RejectRequest.as_view(), name="request-reject"),
    path("citizens/", api.CitizenList.as_view(), name="citizens"),
]
