from urllib.parse import urlparse

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import timezone

from apps.core.models import Click, ShortURL
from apps.core.utils.user_agent import parse_user_agent


def redirect_view(request, slug):
    try:
        short_url = ShortURL.objects.get(slug=slug)
    except ShortURL.DoesNotExist:
        raise Http404

    if not short_url.is_active:
        return HttpResponse(status=410)

    if short_url.expires_at and short_url.expires_at < timezone.now():
        return HttpResponse(status=410)

    if (
        short_url.max_clicks is not None
        and short_url.clicks.count() >= short_url.max_clicks
    ):
        short_url.is_active = False
        short_url.save(update_fields=["is_active"])
        return HttpResponse(status=410)

    # Args are primitives only — promotes to a Celery task without signature changes
    _record_click(
        short_url_id=short_url.pk,
        user_agent_string=request.META.get("HTTP_USER_AGENT", ""),
        referer=request.META.get("HTTP_REFERER", ""),
        utm_source=request.GET.get("utm_source", ""),
        utm_medium=request.GET.get("utm_medium", ""),
        utm_campaign=request.GET.get("utm_campaign", ""),
    )

    return HttpResponseRedirect(short_url.original_url)


def _record_click(
    *, short_url_id, user_agent_string, referer, utm_source, utm_medium, utm_campaign
):
    referrer_domain = urlparse(referer).netloc if referer else ""
    device_type, browser, os = parse_user_agent(user_agent_string)

    Click.objects.create(
        short_url_id=short_url_id,
        device_type=device_type,
        browser=browser,
        os=os,
        referrer_domain=referrer_domain,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
    )
