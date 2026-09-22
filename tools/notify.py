import os
import requests
 
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
RESEND_FROM = os.getenv("RESEND_FROM", "Alex Twin <onboarding@resend.dev>")
RESEND_URL = "https://api.resend.com/emails"
 
 
def send_email(subject: str, body: str):
    """
    Send a notification email to the owner. `body` is plain text; it's wrapped
    in minimal HTML. Returns a short status string (also shown to the model as
    the tool result), never raises.
    """
    if not RESEND_API_KEY or not NOTIFY_EMAIL:
        return "Email not configured (missing RESEND_API_KEY or NOTIFY_EMAIL)."
    try:
        html = "<p>" + body.replace("\n", "<br>") + "</p>"
        resp = requests.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM,
                "to": [NOTIFY_EMAIL],
                "subject": subject,
                "html": html,
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return "Email notification sent."
        return f"Email send failed ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"Email send error: {e}"