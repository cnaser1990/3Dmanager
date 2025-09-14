# calculator/views_license.py
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .licenseing import (
    LICENSE_FILE_PATH,
    get_hw_fingerprint,
    license_status,
    ensure_dirs,
    verify_license,
)

def license_page(request):
    status = license_status()
    
    # Auto-redirect to main app if license is valid
    if status.get("valid"):
        # Optional: add a delay by rendering the page with auto-redirect
        context = {
            "status": status,
            "fingerprint": get_hw_fingerprint(),
            "license_path": LICENSE_FILE_PATH,
            "auto_redirect": True,  # Flag for template to auto-redirect
        }
        return render(request, "calculator/license_page.html", context)
    
    # Show license page normally if not valid
    context = {
        "status": status,
        "fingerprint": get_hw_fingerprint(),
        "license_path": LICENSE_FILE_PATH,
        "auto_redirect": False,
    }
    return render(request, "calculator/license_page.html", context)

@require_POST
def license_upload(request):
    ensure_dirs()
    f = request.FILES.get("file")
    if not f:
        messages.error(request, "No file uploaded.")
        return redirect("license_page")

    # Read uploaded content as UTF-8 text
    try:
        content = f.read().decode("utf-8").strip()
    except UnicodeDecodeError:
        messages.error(request, "Uploaded file is not valid UTF-8 text.")
        return redirect("license_page")

    # Verify before saving so we don't persist an invalid license
    try:
        verify_license(content)
    except PermissionDenied as e:
        messages.error(request, f"Invalid license: {e}")
        return redirect("license_page")

    # Save only after successful verification
    with open(LICENSE_FILE_PATH, "w", encoding="utf-8") as out:
        out.write(content)

    messages.success(request, "License installed successfully.")
    return redirect("calculator:index")  # change 'home' to your main URL name if different

def license_fingerprint(request):
    return HttpResponse(get_hw_fingerprint(), content_type="text/plain")