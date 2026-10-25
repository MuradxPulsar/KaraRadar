"""Notification helpers for watch mode (console + optional webhook)."""
import os
import requests

def alert(domain, score, verdict, threshold=40):
    print(f"[ALERT] {domain} score={score} verdict={verdict}")
    url = os.getenv("KARARADAR_WEBHOOK")
    if url:
        try:
            requests.post(url, json={"domain": domain, "score": score, "verdict": verdict}, timeout=10)
        except Exception:
            pass
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat:
        try:
            msg = f"KaraRadar alert: {domain} score={score} verdict={verdict}"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": msg}, timeout=10)
        except Exception:
            pass
