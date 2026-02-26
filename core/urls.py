from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from . import api

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("health/", views.health, name="health"),
    path("auth/register/", api.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/officer-login/", api.OfficerTokenObtainPairView.as_view(), name="officer_token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", api.MeView.as_view(), name="me"),
    path("profile/", api.ProfileView.as_view(), name="profile"),
    path("profile/password/", api.PasswordChangeView.as_view(), name="profile-password"),
    path("requests/", api.CitizenRequestListCreate.as_view(), name="requests"),
    path("requests/pending/", api.PendingRequestList.as_view(), name="pending-requests"),
    path("requests/approved/", api.ApprovedRequestList.as_view(), name="approved-requests"),
    path("requests/<int:pk>/", api.RequestDetail.as_view(), name="request-detail"),
    path("requests/<int:pk>/resubmit/", api.ResubmitRequest.as_view(), name="request-resubmit"),
    path("requests/<int:pk>/download/", api.RequestDownloadView.as_view(), name="request-download"),
    path("requests/<int:pk>/approve/", api.ApproveRequest.as_view(), name="request-approve"),
    path("requests/<int:pk>/reject/", api.RejectRequest.as_view(), name="request-reject"),
    path("requests/<int:pk>/reopen/", api.ReopenRequest.as_view(), name="request-reopen"),
    path("citizens/", api.CitizenList.as_view(), name="citizens"),
    path("citizens/<int:pk>/", api.CitizenDetailView.as_view(), name="citizen-detail"),
    path("stats/officer/", api.OfficerStatsView.as_view(), name="officer-stats"),
]
