from rest_framework.authentication import SessionAuthentication


class CsrfSessionAuthentication(SessionAuthentication):
    """SessionAuthentication that returns 401 (not 403) for anonymous callers.

    DRF's stock SessionAuthentication defines no ``authenticate_header``, so DRF
    downgrades ``NotAuthenticated`` (401) to ``PermissionDenied`` (403). Both
    Angular apps key their "session expired -> clear + redirect to /login" logic
    on 401, so an expired session otherwise surfaces as broken pages. Returning a
    header string restores the 401; genuine permission denials on an
    authenticated user still return 403.

    ``Session`` is not a real WWW-Authenticate scheme, so no browser triggers a
    native credential dialog for it (only Basic/Digest/NTLM/Negotiate do). CSRF
    enforcement (``enforce_csrf``) is inherited from the parent unchanged.
    """

    def authenticate_header(self, request):
        return "Session"
