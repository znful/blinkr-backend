from urllib.parse import urlparse

from celery import shared_task

from apps.core.models import Click
from apps.core.utils.user_agent import parse_user_agent


@shared_task
def record_click(
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
