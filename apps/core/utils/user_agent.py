import user_agents


def parse_user_agent(user_agent_string: str) -> tuple[str, str, str]:
    if not user_agent_string:
        return "unknown", "", ""

    parsed = user_agents.parse(user_agent_string)

    if parsed.is_bot:
        device_type = "bot"
    elif parsed.is_tablet:
        device_type = "tablet"
    elif parsed.is_mobile:
        device_type = "mobile"
    else:
        device_type = "desktop"

    return device_type, parsed.browser.family or "", parsed.os.family or ""
