"""
Email Utility – SMTP with HTML report + image attachment
=========================================================
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.image     import MIMEImage
from email.mime.base      import MIMEBase
from email                import encoders
from email.utils          import parseaddr
from datetime             import datetime
from flask                import current_app


def send_detection_report(
    recipient_email: str,
    detection_data:  dict,
    result_image_path: str | None = None,
    user_settings = None,
) -> dict:
    """
    Send a road damage detection report via SMTP.

    Parameters
    ----------
    recipient_email   : destination email address
    detection_data    : dict with detection results
    result_image_path : absolute path to annotated result image
    user_settings     : optional UserSettings object or dict to override default SMTP credentials

    Returns
    -------
    {"success": bool, "message": str}
    """
    cfg = current_app.config

    smtp_server   = cfg.get("SMTP_SERVER")
    smtp_port     = cfg.get("SMTP_PORT",   587)
    smtp_user     = cfg.get("SMTP_USERNAME")
    smtp_password = cfg.get("SMTP_PASSWORD")
    smtp_from     = cfg.get("SMTP_FROM",   smtp_user)

    if user_settings:
        def get_val(obj, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(attr) or default
            return getattr(obj, attr, None) or default

        smtp_server   = get_val(user_settings, "smtp_server", smtp_server)
        smtp_port     = get_val(user_settings, "smtp_port", smtp_port)
        smtp_user     = get_val(user_settings, "smtp_username", smtp_user)
        smtp_password = get_val(user_settings, "smtp_password", smtp_password)
        smtp_from     = smtp_user

    # Validate SMTP config
    if not smtp_user or smtp_user == "your_email@gmail.com" or not smtp_password or smtp_password == "your_app_password_here":
        return {"success": False,
                "message": "SMTP not configured. Set SMTP credentials in the Settings page or environment variables."}

    # Build email
    msg = MIMEMultipart("related")
    msg["Subject"] = "🚨 Road Damage Detection Report – RoadGuard AI"
    msg["From"]    = smtp_from
    msg["To"]      = recipient_email
    envelope_from   = parseaddr(smtp_from)[1] or smtp_user

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

            <!-- Image -->
            {"<tr><td style='padding:0 32px;'><img src='cid:result_img' width='100%' style='border-radius:8px;' alt='Detection Result'></td></tr>" if result_image_path and os.path.exists(result_image_path) else ""}

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

    msg_alt = MIMEMultipart("alternative")
    msg_alt.attach(MIMEText(html_body, "html"))
    msg.attach(msg_alt)

    # Attach result image
    if result_image_path and os.path.exists(result_image_path):
        with open(result_image_path, "rb") as img_file:
            img_data = img_file.read()
        img_mime = MIMEImage(img_data)
        img_mime.add_header("Content-ID", "<result_img>")
        img_mime.add_header("Content-Disposition", "inline",
                            filename=os.path.basename(result_image_path))
        msg.attach(img_mime)

    # Send
    try:
        if int(smtp_port) == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
        with server:
            server.ehlo()
            if int(smtp_port) != 465:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(envelope_from, [recipient_email], msg.as_string())
        return {"success": True,
                "message": f"Report sent successfully to {recipient_email}"}
    except smtplib.SMTPAuthenticationError as e:
        return {"success": False,
                "message": f"SMTP authentication failed: {e.smtp_code} {e.smtp_error.decode(errors='ignore') if isinstance(e.smtp_error, bytes) else e.smtp_error}"}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
