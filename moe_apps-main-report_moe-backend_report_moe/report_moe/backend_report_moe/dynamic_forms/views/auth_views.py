from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit_log import log_action
from ..info_querysets import main_sections_queryset_for_user
from ..permissions import LoginRateThrottle
from ..serializers import UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    # Read-only by design: self-service editing of permission flags
    # (can_manage_budget, can_add_user, etc.) has no legitimate use case here —
    # granting/changing those belongs to admin-only flows (UserViewSet), which
    # run privilege-escalation checks this endpoint never did. No frontend
    # code calls PATCH here; it was dead, unguarded write capability.
    #
    # ensure_csrf_cookie: the SPA calls this on startup, so a returning user with
    # a live session but no csrftoken cookie gets one before their first write.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        # Frontend still sends "username"; accept email or legacy username.
        raw = (
            request.data.get("email")
            or request.data.get("username")
            or ""
        )
        identifier = str(raw).strip()
        password = request.data.get("password", "")
        lock_key = f"login_lock_{identifier}"
        attempts_key = f"login_attempts_{identifier}"

        if cache.get(lock_key):
            return Response(
                {
                    "detail": "الحساب مقفل مؤقتاً بسبب محاولات دخول متكررة. حاول بعد 15 دقيقة."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(
            request,
            email=identifier,
            username=identifier,
            password=password,
        )

        if user is None:
            attempts = cache.get(attempts_key, 0) + 1
            if attempts >= 5:
                cache.set(lock_key, True, 60 * 15)
                cache.delete(attempts_key)
                return Response(
                    {
                        "detail": "تم قفل الحساب مؤقتاً بعد 5 محاولات فاشلة. حاول بعد 15 دقيقة."
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            cache.set(attempts_key, attempts, 60 * 15)
            return Response(
                {"detail": "بيانات الدخول غير صحيحة."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(user, "deleted", False):
            return Response(
                {"detail": "بيانات الدخول غير صحيحة."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(lock_key)
        cache.delete(attempts_key)
        login(request, user)
        # "Remember me" unchecked -> session ends when the browser closes.
        # SESSION_EXPIRE_AT_BROWSER_CLOSE is global, so this is per-login.
        if not request.data.get("remember", True):
            request.session.set_expiry(0)
        log_action(request, "LOGIN", details={"login": identifier, "email": user.email})
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_action(request, "LOGOUT")
        logout(request)
        return Response({"detail": "Logged out"})


class UserPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserMainSectionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        u = request.user
        sections = list(main_sections_queryset_for_user(
            u).values("id", "name"))
        return Response({
            "is_admin": bool(u.is_staff or u.is_superuser),
            "main_sections": sections,
        })
