"""Twilio SMS Alert Dispatch Utility."""

import logging
from flask import current_app

logger = logging.getLogger("roadguard.sms")


def send_sms_alert(message_body, user_settings):
    """Send SMS alert using Twilio or simulate if credentials are blank."""
    to_number = user_settings.sms_to
    from_number = user_settings.sms_from
    sid = user_settings.sms_sid
    token = user_settings.sms_token

    # Check if credentials are not fully entered, perform simulation fallback
    if not sid or not token or not from_number or not to_number:
        logger.info("[SMS SIMULATION] Twilio credentials not fully set. Logging message content:")
        logger.info(f"    To: {to_number or 'Not specified'}")
        logger.info(f"    From: {from_number or 'Not specified'}")
        logger.info(f"    Message: {message_body}")
        return True

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        logger.info(f"[SMS ALERT] Sent successfully. SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"[SMS ALERT] Failed to dispatch via Twilio client: {e}")
        return False
