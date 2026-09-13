"""Browsable Swagger UI + OpenAPI document. Public; Try-it-out uses the session."""

from __future__ import annotations

import json

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .openapi import build_openapi


class OpenApiJsonView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return JsonResponse(build_openapi(request), json_dumps_params={"ensure_ascii": False})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SwaggerUiView(View):
    http_method_names = ["get"]

    def get(self, request):
        spec_url = request.build_absolute_uri("/api/docs/openapi.json")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>MOE API — Swagger</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.27.1/swagger-ui.css"/>
  <style>
    html, body {{ margin: 0; background: #fafafa; }}
    .topbar {{ display: none; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.27.1/swagger-ui-bundle.js"></script>
  <script>
    function csrfFromCookie() {{
      const m = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
      return m ? decodeURIComponent(m[1]) : "";
    }}
    window.ui = SwaggerUIBundle({{
      url: {json.dumps(spec_url)},
      dom_id: "#swagger-ui",
      deepLinking: true,
      persistAuthorization: true,
      withCredentials: true,
      requestInterceptor: (req) => {{
        const token = csrfFromCookie();
        if (token) req.headers["X-CSRFToken"] = token;
        req.credentials = "include";
        return req;
      }},
    }});
  </script>
</body>
</html>
"""
        return HttpResponse(html)
