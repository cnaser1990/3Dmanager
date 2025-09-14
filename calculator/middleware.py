# calculator/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import PermissionDenied
from .licenseing import check_license

class LicenseRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        try:
            allow = {
                reverse("license_page"),
                reverse("license_upload"),
                reverse("license_fingerprint"),
            }
        except NoReverseMatch:
            allow = set()

        if path.startswith("/static/") or path == "/favicon.ico":
            return self.get_response(request)
        if path in allow:
            return self.get_response(request)

        try:
            check_license()
        except PermissionDenied:
            try:
                return redirect("license_page")
            except NoReverseMatch:
                pass
        return self.get_response(request)