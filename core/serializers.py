from django.db import transaction
from rest_framework import serializers

from .models import CitizenProfile, User, VerificationRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")


class CitizenProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenProfile
        fields = ("phone", "gender", "age", "address", "nida_number")


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
    profile = CitizenProfileSerializer(required=False, allow_null=True)


class VerificationRequestSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source="citizen.full_name", read_only=True)
    citizen_email = serializers.EmailField(source="citizen.email", read_only=True)
    citizen_phone = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest
        fields = (
            "id",
            "request_type",
            "purpose",
            "additional_info",
            "urgency",
            "status",
            "rejection_reason",
            "decided_at",
            "created_at",
            "updated_at",
            "citizen_name",
            "citizen_email",
            "citizen_phone",
        )
        read_only_fields = (
            "status",
            "rejection_reason",
            "decided_at",
            "created_at",
            "updated_at",
            "citizen_name",
            "citizen_email",
            "citizen_phone",
        )

    def get_citizen_phone(self, obj):
        profile = getattr(obj.citizen, "citizen_profile", None)
        return profile.phone if profile else ""
