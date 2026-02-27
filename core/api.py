from django.utils import timezone
from django.http import HttpResponse
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, VerificationRequest
from .permissions import IsCitizen, IsOfficer, IsOwnerOrOfficer
from .serializers import (
    CitizenProfileSerializer,
    OfficerProfileSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
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
        if request.user.role in {User.Role.OFFICER, User.Role.ADMIN} and hasattr(
            request.user, "officer_profile"
        ):
            profile_data = OfficerProfileSerializer(request.user.officer_profile).data
        return Response({"user": user_data, "profile": profile_data})


class ProfileView(APIView):
    def get(self, request):
        return MeView().get(request)

    def put(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        if "email" in data:
            user.email = data["email"]
        if "full_name" in data:
            user.full_name = data["full_name"]
        update_fields = []
        if "email" in data:
            update_fields.append("email")
        if "full_name" in data:
            update_fields.append("full_name")
        if update_fields:
            user.save(update_fields=update_fields)

        if user.role == User.Role.CITIZEN:
            profile = getattr(user, "citizen_profile", None)
            if profile is None:
                from .models import CitizenProfile

                profile = CitizenProfile.objects.create(
                    user=user,
                    phone=data.get("phone", ""),
                    gender=data.get("gender", CitizenProfile.Gender.MALE),
                    age=data.get("age", 18),
                    address=data.get("address", ""),
                    nida_number=data.get("nida_number", ""),
                )
            else:
                for field in ["phone", "gender", "age", "address", "nida_number"]:
                    if field in data:
                        setattr(profile, field, data[field])
                profile.save()

        if user.role in {User.Role.OFFICER, User.Role.ADMIN}:
            profile = getattr(user, "officer_profile", None)
            if profile is None:
                from .models import OfficerProfile

                profile = OfficerProfile.objects.create(
                    user=user,
                    phone=data.get("phone", ""),
                    position=data.get("position", ""),
                    office=data.get("office", ""),
                )
            else:
                for field in ["phone", "position", "office"]:
                    if field in data:
                        setattr(profile, field, data[field])
                profile.save()

        return MeView().get(request)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated successfully."})


class OfficerStatsView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request):
        today = timezone.localdate()
        pending = VerificationRequest.objects.filter(status=VerificationRequest.Status.PENDING).count()
        approved_today = VerificationRequest.objects.filter(
            status=VerificationRequest.Status.APPROVED,
            decided_at__date=today,
        ).count()
        total_citizens = User.objects.filter(role=User.Role.CITIZEN).count()
        letters_issued = VerificationRequest.objects.filter(status=VerificationRequest.Status.APPROVED).count()
        return Response(
            {
                "pending_requests": pending,
                "approved_today": approved_today,
                "total_citizens": total_citizens,
                "letters_issued": letters_issued,
            }
        )


class OfficerTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role not in {User.Role.OFFICER, User.Role.ADMIN}:
            raise serializers.ValidationError("Not authorized as officer.")
        return data


class OfficerTokenObtainPairView(TokenObtainPairView):
    serializer_class = OfficerTokenSerializer


class CitizenRequestListCreate(generics.ListCreateAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsCitizen]

    def get_queryset(self):
        return VerificationRequest.objects.filter(citizen=self.request.user)

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)


class RequestDetail(generics.RetrieveUpdateAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsOwnerOrOfficer]
    queryset = VerificationRequest.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user != instance.citizen:
            return Response(
                {"detail": "Only the request owner can edit this request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != VerificationRequest.Status.PENDING:
            return Response(
                {"detail": "Only pending requests can be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ResubmitRequest(APIView):
    permission_classes = [IsCitizen]

    def post(self, request, pk: int):
        try:
            req = VerificationRequest.objects.get(pk=pk, citizen=request.user)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if req.status != VerificationRequest.Status.REJECTED:
            return Response(
                {"detail": "Only rejected requests can be resubmitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "request_type" in request.data and request.data.get("request_type") != req.request_type:
            return Response(
                {"detail": "Request type cannot be changed when resubmitting."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VerificationRequestSerializer(req, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            status=VerificationRequest.Status.PENDING,
            rejection_reason="",
            decided_by=None,
            decided_at=None,
        )
        return Response(serializer.data)


class RequestDownloadView(APIView):
    permission_classes = [IsOwnerOrOfficer]

    def get(self, request, pk: int):
        try:
            req = VerificationRequest.objects.get(pk=pk)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if req.status != VerificationRequest.Status.APPROVED:
            return Response({"detail": "Request is not approved yet."}, status=status.HTTP_400_BAD_REQUEST)

        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.utils import simpleSplit
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin_x = 2 * cm
        margin_right = width - 2 * cm
        content_width = margin_right - margin_x

        def draw_center(y, text, size=11, bold=False):
            pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            pdf.drawCentredString(width / 2, y, text)

        def draw_wrapped(text, x, y, max_width, size=10, leading=14):
            pdf.setFont("Helvetica", size)
            lines = simpleSplit(text, "Helvetica", size, max_width)
            for line_text in lines:
                pdf.drawString(x, y, line_text)
                y -= leading
            return y

        def draw_field(y, label, value):
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(margin_x, y, f"{label}:")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin_x + 4.2 * cm, y, value)
            pdf.setLineWidth(0.3)
            pdf.line(margin_x + 4.2 * cm, y - 1.5, margin_right, y - 1.5)
            return y - 0.6 * cm

        meta = req.metadata or {}
        citizen = req.citizen
        profile = getattr(citizen, "citizen_profile", None)

        def safe(value, fallback="........................"):
            if value is None:
                return fallback
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed if trimmed else fallback
            return str(value)

        def title_case(value):
            text = safe(value, "")
            return text.title() if text else "........................"

        subject_map = {
            "residence": "UTAMBULISHO WA MKAZI",
            "nida": "UTAMBULISHO WA NIDA",
            "license": "UTAMBULISHO WA LESENI",
        }

        header_y = height - 2.2 * cm
        draw_center(header_y, "JAMHURI YA MUUNGANO WA TANZANIA", 12, True)
        draw_center(header_y - 0.6 * cm, "OFISI YA RAIS", 11, True)
        draw_center(header_y - 1.2 * cm, "TAWALA ZA MIKOA NA SERIKALI ZA MITAA", 11, True)
        draw_center(header_y - 1.8 * cm, "HALMASHAURI YA MANISPAA YA MUSOMA", 11, True)
        pdf.setLineWidth(0.6)
        pdf.line(margin_x, header_y - 2.3 * cm, margin_right, header_y - 2.3 * cm)

        # Photo placeholder
        photo_x = margin_x
        photo_y = height - 8.2 * cm
        pdf.rect(photo_x, photo_y, 4 * cm, 5 * cm)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(photo_x + 2 * cm, photo_y + 2.8 * cm, "BANDIKA")
        pdf.drawCentredString(photo_x + 2 * cm, photo_y + 2.4 * cm, "PICHA")
        pdf.drawCentredString(photo_x + 2 * cm, photo_y + 2.0 * cm, "HAPA")

        # Right address block
        pdf.setFont("Helvetica", 9)
        right_x = width - 8.8 * cm
        pdf.drawString(right_x, height - 6.2 * cm, "OFISI YA SERIKALI ZA MTAA,")
        pdf.drawString(right_x, height - 6.7 * cm, f"MTAA WA {title_case(meta.get('mtaa'))}")
        pdf.drawString(right_x, height - 7.2 * cm, f"KATA {title_case(meta.get('ward'))}")
        pdf.drawString(right_x, height - 7.7 * cm, f"WILAYA {title_case(meta.get('district'))}")
        pdf.drawString(right_x, height - 8.2 * cm, f"MKOA {title_case(meta.get('region'))}")
        pdf.drawString(right_x, height - 8.8 * cm, f"TAREHE: {safe(meta.get('letter_date'), '___/___/_____')}")

        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(
            margin_x,
            height - 9.3 * cm,
            f"KUMBUKUMBU NA: {safe(meta.get('reference_no'), 'SM/SN/KN/____')}",
        )
        pdf.setFont("Helvetica", 10)
        pdf.drawString(
            margin_x,
            height - 10.0 * cm,
            f"KWA: {safe(meta.get('to'), 'Husika / Yeyote Anayehusika')}",
        )

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(
            width / 2,
            height - 11.2 * cm,
            f"YAH: {subject_map.get(req.request_type, 'UTAMBULISHO WA MKAZI')}",
        )

        body_y = height - 12.4 * cm
        body_y = draw_wrapped(
            "Husika na kichwa cha habari tajwa hapo juu.",
            margin_x,
            body_y,
            content_width,
        )
        body_y = draw_wrapped(
            "Naomba kutambulisha na kumthibitisha ya kwamba ndugu:",
            margin_x,
            body_y - 2,
            content_width,
        )

        name = citizen.full_name
        dob = safe(meta.get("birth_date"), "___/___/_____")
        phone = profile.phone if profile else meta.get("phone", "")
        address = profile.address if profile else meta.get("address", "")
        ward = title_case(meta.get("ward"))
        mtaa = title_case(meta.get("mtaa"))
        region = title_case(meta.get("region"))
        district = title_case(meta.get("district"))
        house_no = safe(meta.get("house_no"), "______")
        occupation = safe(meta.get("occupation"), "______")
        stay = safe(meta.get("stay_duration"), "______")

        y = body_y - 12
        y = draw_field(y, "Jina", safe(name, "........................"))
        y = draw_field(y, "Amezaliwa", dob)
        y = draw_field(y, "Namba ya simu", phone or "______")
        y = draw_field(y, "Kazi", occupation)
        y = draw_field(y, "Anaishi", address or "______")
        y = draw_field(y, "Mtaa", mtaa)
        y = draw_field(y, "Kata", ward)
        y = draw_field(y, "Wilaya", district)
        y = draw_field(y, "Mkoa", region)
        y = draw_field(y, "Nyumba No", house_no)
        y = draw_field(y, "Muda wa Makazi", stay)

        y = draw_wrapped(
            f"Sababu ya barua: {safe(req.purpose, '______')}",
            margin_x,
            y - 4,
            content_width,
        )
        y = draw_wrapped(
            "Maelezo hayo hapo juu ni sahihi kwa kadri ya taarifa tulizonazo.",
            margin_x,
            y - 2,
            content_width,
        )
        y = draw_wrapped(
            "Hivyo basi naomba apatiwe huduma anayoiomba.",
            margin_x,
            y - 2,
            content_width,
        )

        pdf.setFont("Helvetica", 10)
        pdf.drawString(
            margin_x,
            y - 12,
            "Imesainiwa na: ________________________________   Mhuri: ______________",
        )
        pdf.drawString(
            margin_x,
            y - 24,
            "Jina la Afisa: ________________________________   Saini: ______________",
        )

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        filename = f"mtaa-letter-{req.id}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class PendingRequestList(generics.ListAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsOfficer]

    def get_queryset(self):
        return VerificationRequest.objects.filter(status=VerificationRequest.Status.PENDING)


class ApprovedRequestList(generics.ListAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsOfficer]

    def get_queryset(self):
        return VerificationRequest.objects.filter(status=VerificationRequest.Status.APPROVED)


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


class ReopenRequest(APIView):
    permission_classes = [IsOfficer]

    def post(self, request, pk: int):
        try:
            req = VerificationRequest.objects.get(pk=pk)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if req.status == VerificationRequest.Status.PENDING:
            return Response({"detail": "Request is already pending."}, status=status.HTTP_400_BAD_REQUEST)

        req.status = VerificationRequest.Status.PENDING
        req.rejection_reason = ""
        req.decided_by = None
        req.decided_at = None
        req.save(update_fields=["status", "rejection_reason", "decided_by", "decided_at", "updated_at"])
        return Response(VerificationRequestSerializer(req).data)


class CitizenList(generics.ListAPIView):
    permission_classes = [IsOfficer]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role=User.Role.CITIZEN)


class CitizenDetailView(APIView):
    permission_classes = [IsOfficer]

    def get(self, request, pk: int):
        try:
            citizen = User.objects.get(pk=pk, role=User.Role.CITIZEN)
        except User.DoesNotExist:
            return Response({"detail": "Citizen not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(citizen, "citizen_profile", None)
        data = {
            "user": UserSerializer(citizen).data,
            "profile": CitizenProfileSerializer(profile).data if profile else None,
        }
        return Response(data)
