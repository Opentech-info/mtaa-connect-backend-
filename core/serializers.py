from django.db import transaction
from rest_framework import serializers

from .models import CitizenProfile, OfficerProfile, User, VerificationRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")


class CitizenProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenProfile
        fields = ("phone", "gender", "age", "address", "nida_number")


class OfficerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficerProfile
        fields = ("phone", "position", "office")


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)
    gender = serializers.ChoiceField(choices=CitizenProfile.Gender.choices)
    age = serializers.IntegerField(min_value=18, max_value=120)
    address = serializers.CharField(max_length=255)
    nida_number = serializers.CharField(max_length=30, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        phone = validated_data.pop("phone")
        gender = validated_data.pop("gender")
        age = validated_data.pop("age")
        address = validated_data.pop("address")
        nida_number = validated_data.pop("nida_number", "")

        user = User.objects.create_user(
            role=User.Role.CITIZEN,
            password=password,
            **validated_data,
        )
        CitizenProfile.objects.create(
            user=user,
            phone=phone,
            gender=gender,
            age=age,
            address=address,
            nida_number=nida_number,
        )
        return user


class MeSerializer(serializers.Serializer):
    user = UserSerializer()
    profile = serializers.DictField(required=False, allow_null=True)


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(required=False, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    gender = serializers.ChoiceField(
        choices=CitizenProfile.Gender.choices, required=False
    )
    age = serializers.IntegerField(required=False, min_value=18, max_value=120)
    address = serializers.CharField(required=False, max_length=255)
    nida_number = serializers.CharField(required=False, allow_blank=True, max_length=30)
    position = serializers.CharField(required=False, allow_blank=True, max_length=100)
    office = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already in use.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs


class VerificationRequestSerializer(serializers.ModelSerializer):
    citizen_id = serializers.IntegerField(source="citizen.id", read_only=True)
    citizen_name = serializers.CharField(source="citizen.full_name", read_only=True)
    citizen_email = serializers.EmailField(source="citizen.email", read_only=True)
    citizen_phone = serializers.SerializerMethodField()
    citizen_address = serializers.SerializerMethodField()
    citizen_gender = serializers.SerializerMethodField()
    citizen_age = serializers.SerializerMethodField()
    citizen_nida = serializers.SerializerMethodField()

    metadata = serializers.JSONField(required=False)

    class Meta:
        model = VerificationRequest
        fields = (
            "id",
            "request_type",
            "purpose",
            "additional_info",
            "metadata",
            "urgency",
            "status",
            "rejection_reason",
            "decided_at",
            "created_at",
            "updated_at",
            "citizen_id",
            "citizen_name",
            "citizen_email",
            "citizen_phone",
            "citizen_address",
            "citizen_gender",
            "citizen_age",
            "citizen_nida",
        )
        read_only_fields = (
            "status",
            "rejection_reason",
            "decided_at",
            "created_at",
            "updated_at",
            "citizen_id",
            "citizen_name",
            "citizen_email",
            "citizen_phone",
            "citizen_address",
            "citizen_gender",
            "citizen_age",
            "citizen_nida",
        )

    def get_citizen_phone(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.phone if profile else ""

    def get_citizen_address(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.address if profile else ""

    def get_citizen_gender(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.gender if profile else ""

    def get_citizen_age(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.age if profile else None

    def get_citizen_nida(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.nida_number if profile else ""

    def validate(self, attrs):
        request_type = attrs.get("request_type") or getattr(self.instance, "request_type", None)
        purpose = attrs.get("purpose")
        if purpose is not None and not str(purpose).strip():
            raise serializers.ValidationError({"purpose": "This field may not be blank."})

        existing_meta = getattr(self.instance, "metadata", {}) if self.instance else {}
        incoming_meta = attrs.get("metadata")
        if incoming_meta is None:
            metadata = existing_meta or {}
        else:
            # Merge so partial updates keep previously provided values while allowing overrides.
            metadata = {**existing_meta, **incoming_meta}
        attrs["metadata"] = metadata
        required_fields = [
            "reference_no",
            "to",
            "ward",
            "mtaa",
            "region",
            "district",
            "house_no",
            "birth_date",
            "occupation",
            "stay_duration",
            "letter_date",
        ]
        errors = {}
        for field in required_fields:
            value = metadata.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors[field] = "This field is required."
        if errors and request_type in {
            VerificationRequest.RequestType.RESIDENCE,
            VerificationRequest.RequestType.NIDA,
            VerificationRequest.RequestType.LICENSE,
        }:
            raise serializers.ValidationError({"metadata": errors})
        return attrs


class CitizenDetailSerializer(serializers.Serializer):
    user = UserSerializer()
    profile = CitizenProfileSerializer(allow_null=True)
