"""Block delete (soft or hard) when related rows still exist."""

from rest_framework.exceptions import ValidationError


def raise_if_blocked(blockers: list[str], entity_label_ar: str) -> None:
    if not blockers:
        return
    joined = "، ".join(blockers)
    raise ValidationError(
        {"detail": f"لا يمكن حذف {entity_label_ar} لوجود ارتباطات: {joined}."}
    )
