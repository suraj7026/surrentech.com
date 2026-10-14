from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import ConsultRequest

EMAIL_OK = r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$"


@require_GET
def home(request):
    return render(request, "website/home.html", {"sent": request.GET.get("sent") == "1"})


@require_POST
def consult(request):
    import re

    email = (request.POST.get("email") or "").strip().lower()
    if (request.POST.get("website") or "").strip():  # honeypot: bots only
        return redirect("/?sent=1#contact")
    if re.match(EMAIL_OK, email):
        ConsultRequest.objects.create(
            email=email,
            remote_addr=request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    return redirect("/?sent=1#contact")


@require_GET
def health(request):
    return HttpResponse("ok", content_type="text/plain")
