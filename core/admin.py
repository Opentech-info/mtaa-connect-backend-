from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import CitizenProfile, OfficerProfile, User, VerificationRequest


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "full_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "full_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )

    USERNAME_FIELD = "email"
    filter_horizontal = ("groups", "user_permissions")


@admin.register(CitizenProfile)
class CitizenProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "gender", "age")
    search_fields = ("user__email", "user__full_name", "phone", "nida_number")


@admin.register(OfficerProfile)
class OfficerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "position", "office")
    search_fields = ("user__email", "user__full_name", "phone")


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "request_type", "citizen", "status", "created_at", "decided_at")
    list_filter = ("status", "request_type", "urgency")
    search_fields = ("citizen__email", "citizen__full_name", "purpose")
