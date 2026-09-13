"""Shared email uniqueness helpers for user creation."""

from django.contrib.auth import get_user_model

User = get_user_model()


def unique_email(desired: str, parent=None) -> str:
    """Return a normalized email if free globally.

    Parent is accepted for call-site compatibility; uniqueness is global.
    """
    email = (desired or "").strip()
    if not email:
        return email
    if not User.objects.filter(email__iexact=email).exists():
        return email
    # Should not be reached when callers assert availability first.
    if parent is not None:
        local, sep, domain = email.partition("@")
        if sep and domain:
            candidate = f"{local}_{parent.id}@{domain}"
            n = 2
            while User.objects.filter(email__iexact=candidate).exists():
                candidate = f"{local}_{parent.id}_{n}@{domain}"
                n += 1
            return candidate
    raise ValueError(f"Email already taken: {email}")


def assert_email_available_for_parent(parent, desired: str) -> None:
    """Raise if the email is already used by a live user.

    Parent is accepted for call-site compatibility; uniqueness is global.
    """
    from rest_framework.exceptions import ValidationError

    email = (desired or "").strip()
    if not email:
        raise ValidationError({"email": "Email is required."})
    clash = User.objects.filter(deleted=False, email__iexact=email).exists()
    if clash:
        raise ValidationError({"email": "This email is already in use."})


# Backward-compatible aliases
unique_username = unique_email
assert_username_available_for_parent = assert_email_available_for_parent
