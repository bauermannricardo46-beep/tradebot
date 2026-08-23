from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .notifications import public_key, remove_subscription, save_subscription, send_push, subscriptions, vapid_configured

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict[str, str]


class TestNotification(BaseModel):
    title: str = "TradeBot AI"
    body: str = "Test-Benachrichtigung"
    url: str = "/"


@router.get("/config")
def notification_config():
    return {"supported": True, "push_configured": vapid_configured(), "subscribers": len(subscriptions), "public_key": public_key()}


@router.post("/subscribe")
def subscribe(subscription: PushSubscription):
    save_subscription(subscription.model_dump())
    return {"ok": True, "subscribers": len(subscriptions)}


@router.delete("/subscribe")
def unsubscribe(endpoint: str):
    return {"ok": remove_subscription(endpoint), "subscribers": len(subscriptions)}


@router.post("/test")
def test_notification(payload: TestNotification):
    return send_push(payload.title, payload.body, payload.url)
