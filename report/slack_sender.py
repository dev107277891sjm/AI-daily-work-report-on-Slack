"""
Send report text to Slack via Incoming Webhook.
"""
import requests


def send_report_to_slack(webhook_url: str, report_text: str) -> bool:
    """
    POST report to Slack. Returns True on success, False on failure.
    """
    try:
        resp = requests.post(
            webhook_url,
            json={"text": report_text},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False
