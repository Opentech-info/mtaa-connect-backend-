from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        OFFICER = "officer", "Officer"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CITIZEN)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self) -> str:
        return self.email


class CitizenProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="citizen_profile")
    phone = models.CharField(max_length=30)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    age = models.PositiveSmallIntegerField()
    address = models.CharField(max_length=255)
    nida_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.full_name} Profile"


class OfficerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="officer_profile")
    phone = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=100, blank=True)
    office = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.full_name} Officer"


class VerificationRequest(models.Model):
    class RequestType(models.TextChoices):
        RESIDENCE = "residence", "Residence Letter"
        NIDA = "nida", "NIDA Verification"
        LICENSE = "license", "License Verification"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Urgency(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENT = "urgent", "Urgent"

    citizen = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="requests",
        limit_choices_to={"role": User.Role.CITIZEN},
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    purpose = models.CharField(max_length=255)
    additional_info = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions",
        limit_choices_to={"role__in": [User.Role.OFFICER, User.Role.ADMIN]},
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.request_type} - {self.citizen.full_name}"
