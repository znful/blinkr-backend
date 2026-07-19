from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import timezone

from apps.core.models import ShortURL
from apps.core.tasks import record_click


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

    record_click.delay(
        short_url_id=short_url.pk,
        user_agent_string=request.META.get("HTTP_USER_AGENT", ""),
        referer=request.META.get("HTTP_REFERER", ""),
        utm_source=request.GET.get("utm_source", ""),
        utm_medium=request.GET.get("utm_medium", ""),
        utm_campaign=request.GET.get("utm_campaign", ""),
    )

    return HttpResponseRedirect(short_url.original_url)
