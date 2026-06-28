import uuid


def generate_slug() -> str:
    return uuid.uuid4().hex[:8]
