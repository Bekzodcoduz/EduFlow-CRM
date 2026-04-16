"""SMS yuborish: dry_run (standart), console (log), webhook (tashqi xizmat)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def send_bulk(phones: list[str], text: str) -> dict[str, Any]:
    """
    phones: normalizatsiya qilingan raqamlar ro'yxati.
    Qaytadi: {ok: bool, sent: int, mode: str, detail: str}
    """
    backend = getattr(settings, "SMS_BACKEND", "dry_run")
    if backend == "console":
        return _send_console(phones, text)
    if backend == "webhook":
        return _send_webhook(phones, text)
    return _send_dry_run(phones, text)


def _send_dry_run(phones: list[str], text: str) -> dict[str, Any]:
    return {
        "ok": True,
        "sent": 0,
        "mode": "dry_run",
        "detail": (
            f"{len(phones)} ta raqam, {len(text)} belgi — SMS_BACKEND=dry_run, "
            "xabar yuborilmadi. Haqiqiy yuborish uchun .env da SMS_BACKEND ni o'zgartiring."
        ),
    }


def _send_console(phones: list[str], text: str) -> dict[str, Any]:
    for p in phones:
        logger.info("[SMS console] %s | %s", p, text)
    return {
        "ok": True,
        "sent": len(phones),
        "mode": "console",
        "detail": f"{len(phones)} ta SMS jurnalga yozildi (logging).",
    }


def _send_webhook(phones: list[str], text: str) -> dict[str, Any]:
    url = (getattr(settings, "SMS_WEBHOOK_URL", None) or "").strip()
    if not url:
        return {
            "ok": False,
            "sent": 0,
            "mode": "webhook",
            "detail": "SMS_WEBHOOK_URL bo'sh — .env ni tekshiring.",
        }

    secret = (getattr(settings, "SMS_WEBHOOK_SECRET", None) or "").strip()
    payload = json.dumps(
        {"phones": phones, "message": text},
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **({"X-Webhook-Secret": secret} if secret else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:500]
        return {
            "ok": False,
            "sent": 0,
            "mode": "webhook",
            "detail": f"HTTP {e.code}: {err_body or e.reason}",
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "sent": 0,
            "mode": "webhook",
            "detail": f"Ulanish xatosi: {e.reason!s}",
        }

    if 200 <= code < 300:
        return {
            "ok": True,
            "sent": len(phones),
            "mode": "webhook",
            "detail": f"Webhook javob: HTTP {code}. {body[:200]}",
        }
    return {
        "ok": False,
        "sent": 0,
        "mode": "webhook",
        "detail": f"Kutilmagan HTTP {code}: {body[:300]}",
    }
