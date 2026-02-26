from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, VerificationRequest
from .permissions import IsCitizen, IsOfficer, IsOwnerOrOfficer
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    VerificationRequestSerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        user_data = UserSerializer(request.user).data
        profile_data = None
        if request.user.role == User.Role.CITIZEN and hasattr(request.user, "citizen_profile"):
            profile_data = {
                "phone": request.user.citizen_profile.phone,
                "gender": request.user.citizen_profile.gender,
                "age": request.user.citizen_profile.age,
                "address": request.user.citizen_profile.address,
                "nida_number": request.user.citizen_profile.nida_number,
            }
        return Response({"user": user_data, "profile": profile_data})


class CitizenRequestListCreate(generics.ListCreateAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsCitizen]

    def get_queryset(self):
        return VerificationRequest.objects.filter(citizen=self.request.user)

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)


class RequestDetail(generics.RetrieveAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsOwnerOrOfficer]
    queryset = VerificationRequest.objects.all()


class PendingRequestList(generics.ListAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsOfficer]

    def get_queryset(self):
        return VerificationRequest.objects.filter(status=VerificationRequest.Status.PENDING)


class ApproveRequest(APIView):
    permission_classes = [IsOfficer]

    def post(self, request, pk: int):
        try:
            req = VerificationRequest.objects.get(pk=pk)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        req.status = VerificationRequest.Status.APPROVED
        req.rejection_reason = ""
        req.decided_by = request.user
        req.decided_at = timezone.now()
        req.save(update_fields=["status", "rejection_reason", "decided_by", "decided_at", "updated_at"])
        return Response(VerificationRequestSerializer(req).data)


class RejectRequest(APIView):
    permission_classes = [IsOfficer]

    def post(self, request, pk: int):
        try:
            req = VerificationRequest.objects.get(pk=pk)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get("reason", "").strip()
        if not reason:
            reason = "No reason provided."

        req.status = VerificationRequest.Status.REJECTED
        req.rejection_reason = reason
        req.decided_by = request.user
        req.decided_at = timezone.now()
        req.save(update_fields=["status", "rejection_reason", "decided_by", "decided_at", "updated_at"])
        return Response(VerificationRequestSerializer(req).data)


class CitizenList(generics.ListAPIView):
    permission_classes = [IsOfficer]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role=User.Role.CITIZEN)
