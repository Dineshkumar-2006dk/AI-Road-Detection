"""
Email Utility – Brevo HTTP API with HTML report + image attachment
=========================================================
"""

import os
import base64
import requests
from datetime             import datetime
from flask                import current_app


def send_detection_report(
    recipient_email: str,
    detection_data:  dict,
    result_image_path: str | None = None,
    user_settings = None,
) -> dict:
    """
    Send a road damage detection report via Brevo Transactional Email HTTP API.

    Parameters
    ----------
    recipient_email   : destination email address
    detection_data    : dict with detection results
    result_image_path : absolute path to annotated result image
    user_settings     : optional UserSettings object or dict to override default Brevo credentials

    Returns
    -------
    {"success": bool, "message": str}
    """
    cfg = current_app.config

    brevo_api_key = cfg.get("BREVO_API_KEY") or cfg.get("SMTP_PASSWORD") or ""
    sender_email  = cfg.get("BREVO_SENDER_EMAIL") or cfg.get("SMTP_USERNAME") or ""
    sender_name   = cfg.get("BREVO_SENDER_NAME") or cfg.get("SMTP_SERVER") or "RoadGuard AI"

    if user_settings:
        def get_val(obj, attr, default=None):
            if isinstance(obj, dict):
                v = obj.get(attr)
            else:
                v = getattr(obj, attr, None)
            return v if (v is not None and str(v).strip() != "") else default

        sender_name   = get_val(user_settings, "smtp_server", sender_name)
        sender_email  = get_val(user_settings, "smtp_username", sender_email)
        brevo_api_key = get_val(user_settings, "smtp_password", brevo_api_key)

    # Validate Brevo config
    if not brevo_api_key or brevo_api_key in ("your_app_password_here", "") or not sender_email or sender_email in ("your_email@gmail.com", ""):
        return {
            "success": False,
            "message": "Brevo HTTP API not configured. Please set your Brevo API Key and Sender Email in the Settings page or Render environment variables."
        }

    now       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    condition = detection_data.get("road_condition", "Unknown")
    severity  = detection_data.get("severity",       "Unknown")
    damage    = ", ".join(detection_data.get("damage_types", [])) or "No damage detected"
    conf      = detection_data.get("avg_confidence", 0) * 100
    lat       = detection_data.get("latitude",  "N/A")
    lon       = detection_data.get("longitude", "N/A")
    maps_link = detection_data.get("maps_link", "#")
    location  = detection_data.get("location_name", f"{lat}, {lon}")

    cond_color = {
        "Good":     "#28a745",
        "Moderate": "#ffc107",
        "Poor":     "#fd7e14",
        "Critical": "#dc3545",
    }.get(condition, "#6c757d")

    sev_color = {
        "Low":      "#28a745",
        "Medium":   "#ffc107",
        "High":     "#fd7e14",
        "Critical": "#dc3545",
    }.get(severity, "#6c757d")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>RoadGuard AI Report</title></head>
    <body style="margin:0;padding:0;background:#0d1117;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:20px 0;">
          <table width="640" cellpadding="0" cellspacing="0"
                 style="background:#161b22;border-radius:12px;overflow:hidden;
                        box-shadow:0 4px 24px rgba(0,0,0,0.4);">

            <!-- Header -->
            <tr><td style="background:linear-gradient(135deg,#1565c0,#0d47a1);
                           padding:32px;text-align:center;">
              <h1 style="margin:0;color:#fff;font-size:26px;">🛡️ RoadGuard AI</h1>
              <p  style="margin:6px 0 0;color:#90caf9;font-size:14px;">
                  Road Damage Detection Report</p>
            </td></tr>

            <!-- Alert badge -->
            <tr><td style="padding:20px 32px 0;">
              <div style="background:{cond_color};border-radius:8px;padding:12px 20px;
                          text-align:center;">
                <span style="color:#fff;font-size:18px;font-weight:bold;">
                  Road Condition: {condition}
                </span>
              </div>
            </td></tr>

            <!-- Details table -->
            <tr><td style="padding:24px 32px;">
              <table width="100%" cellspacing="0"
                     style="border-collapse:collapse;color:#e0e0e0;font-size:14px;">
                {"".join(f'''
                <tr style="border-bottom:1px solid #21262d;">
                  <td style="padding:10px 8px;color:#8b949e;width:40%;">{k}</td>
                  <td style="padding:10px 8px;font-weight:bold;">{v}</td>
                </tr>''' for k,v in [
                    ("📅 Date & Time",   now),
                    ("⚠️  Severity",      f'<span style="color:{sev_color};">{severity}</span>'),
                    ("🔍 Damage Types",  damage),
                    ("📊 Confidence",    f"{conf:.1f}%"),
                    ("📍 Location",      location),
                    ("🌐 Coordinates",   f"{lat}, {lon}"),
                ])}
              </table>
            </td></tr>

            <!-- Maps link -->
            <tr><td style="padding:0 32px 16px;text-align:center;">
              <a href="{maps_link}" style="display:inline-block;background:#1565c0;
                 color:#fff;padding:10px 28px;border-radius:6px;
                 text-decoration:none;font-size:13px;">
                📍 View on Google Maps
              </a>
            </td></tr>

            <!-- Image Note -->
            {"<tr><td style='padding:16px 32px;color:#8b949e;text-align:center;font-size:13px;'>📎 The annotated detection image is attached to this email.</td></tr>" if result_image_path and os.path.exists(result_image_path) else ""}

            <!-- Footer -->
            <tr><td style="padding:24px 32px;text-align:center;
                           border-top:1px solid #21262d;">
              <p style="margin:0;color:#8b949e;font-size:12px;">
                Generated by <b style="color:#90caf9;">RoadGuard AI</b> |
                AI-Based Road Quality Monitoring System<br>
                {now}
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": "🚨 Road Damage Detection Report – RoadGuard AI",
        "htmlContent": html_body
    }

    if result_image_path and os.path.exists(result_image_path):
        try:
            with open(result_image_path, "rb") as img_file:
                img_data = img_file.read()
            encoded_img = base64.b64encode(img_data).decode("utf-8")
            payload["attachment"] = [
                {
                    "name": os.path.basename(result_image_path),
                    "content": encoded_img
                }
            ]
        except Exception as e:
            current_app.logger.warning(f"Failed to read/encode attachment: {e}")

    headers = {
        "api-key": brevo_api_key,
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    try:
        # Retry once on network/timeout errors (Render cold-start or transient failure)
        last_err = None
        for attempt in range(2):
            try:
                response = requests.post(
                    "https://api.brevo.com/v3/smtp/email",
                    json=payload, headers=headers, timeout=20
                )
                break
            except requests.exceptions.Timeout:
                last_err = "Request timed out"
                if attempt == 0:
                    import time; time.sleep(2)
            except requests.exceptions.ConnectionError as ce:
                last_err = f"Connection error: {ce}"
                if attempt == 0:
                    import time; time.sleep(2)
        else:
            return {"success": False, "message": f"Email network error after retry: {last_err}"}

        if response.status_code in (200, 201, 202):
            return {"success": True, "message": f"Report sent successfully to {recipient_email}"}
        else:
            try:
                err_msg = response.json().get("message", response.text)
            except Exception:
                err_msg = response.text
            # Special guidance for IP restriction error
            if "unrecognised IP" in err_msg or response.status_code == 401:
                err_msg = (
                    f"Brevo API error ({response.status_code}): IP not whitelisted. "
                    "Go to Brevo → My Account → Security → Authorised IPs → "
                    "click 'Deactivate' to allow all IPs (needed for Render which changes IPs on restart)."
                )
            return {"success": False, "message": err_msg}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
