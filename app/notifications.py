from __future__ import annotations

import json
import os
from typing import Any

subscriptions: dict[str, dict[str, Any]] = {}


def save_subscription(subscription: dict[str, Any]) -> str:
    endpoint = subscription.get("endpoint")
    if not endpoint:
        raise ValueError("subscription endpoint missing")
    subscriptions[endpoint] = subscription
    return endpoint


def remove_subscription(endpoint: str) -> bool:
    return subscriptions.pop(endpoint, None) is not None


def vapid_configured() -> bool:
    return all(os.getenv(k) for k in ("VAPID_PRIVATE_KEY", "VAPID_CLAIMS_EMAIL", "VAPID_PUBLIC_KEY"))


def public_key() -> str | None:
    return os.getenv("VAPID_PUBLIC_KEY") or None


def send_push(title: str, body: str, url: str = "/") -> dict[str, int | bool]:
    if not vapid_configured():
        return {"sent": 0, "skipped": len(subscriptions), "configured": False}

    from pywebpush import WebPushException, webpush

    sent = 0
    dead: list[str] = []
    for endpoint, subscription in list(subscriptions.items()):
        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
                vapid_claims={"sub": os.environ["VAPID_CLAIMS_EMAIL"]},
            )
            sent += 1
        except WebPushException as exc:
            if getattr(exc, "response", None) is not None and getattr(exc.response, "status_code", 0) in (404, 410):
                dead.append(endpoint)
    for endpoint in dead:
        subscriptions.pop(endpoint, None)
    return {"sent": sent, "skipped": len(subscriptions) - sent, "configured": True}
