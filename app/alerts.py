from flask_mail import Message
from app import mail
import threading


LEVEL_COLORS  = {'LOW': '#10b981', 'MODERATE': '#f59e0b', 'HIGH': '#f97316', 'CRITICAL': '#ef4444'}
LEVEL_BANNERS = {'LOW': '#0d280d', 'MODERATE': '#281e0d', 'HIGH': '#281a0d', 'CRITICAL': '#280d0d'}
SEVERITY_COLORS = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}


def _build_email(user_email, user_threshold, weather_data, risk_data, timestamp):
    level      = risk_data.get('level', 'HIGH')
    color      = LEVEL_COLORS.get(level, '#f97316')
    banner_bg  = LEVEL_BANNERS.get(level, '#280d0d')
    city       = weather_data.get('city', 'Unknown')
    score      = risk_data.get('score', '--')
    desc       = weather_data.get('description', '--')
    temp       = weather_data.get('temperature', '--')
    feels      = weather_data.get('feels_like', '--')
    humidity   = weather_data.get('humidity', '--')
    wind       = weather_data.get('wind_speed', '--')
    pressure   = weather_data.get('pressure', '--')
    visibility = weather_data.get('visibility', '--')
    risk_desc  = risk_data.get('description', '')

    factors_html = ''.join(
        '<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1e2d3d22;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{SEVERITY_COLORS.get(f["severity"], "#6b8090")};flex-shrink:0;display:inline-block;"></span>'
        f'<span style="font-size:13px;color:#c8d8e8;flex:1;">{f["name"]}</span>'
        f'<span style="font-size:12px;color:#6b8090;font-family:monospace;">{f["value"]}</span>'
        '</div>'
        for f in risk_data.get('factors', [])
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/>
<style>
body{{margin:0;padding:0;background:#080c14;font-family:'Segoe UI',sans-serif;color:#c8d8e8;}}
.wrapper{{max-width:600px;margin:0 auto;padding:32px 16px;}}
.header{{text-align:center;padding:24px;background:linear-gradient(135deg,#0d1420,#111827);
         border:1px solid #1e2d3d;border-radius:16px 16px 0 0;border-bottom:none;}}
.logo{{font-family:monospace;font-size:22px;font-weight:700;letter-spacing:4px;color:#fff;}}
.sub{{font-size:11px;letter-spacing:2px;color:#4b6070;margin-top:4px;}}
.body{{background:#0d1420;border:1px solid #1e2d3d;border-radius:0 0 16px 16px;padding:28px;}}
.stat{{background:#080c14;border:1px solid #1e2d3d;border-radius:10px;padding:14px;}}
.stat-label{{font-size:11px;color:#4b6070;letter-spacing:1px;margin-bottom:4px;}}
.stat-value{{font-size:18px;font-weight:600;color:#fff;font-family:monospace;}}
.btn{{display:inline-block;margin-top:12px;padding:10px 24px;
      background:linear-gradient(135deg,#00d4ff,#0099bb);color:#000;
      font-family:monospace;font-size:12px;font-weight:700;text-decoration:none;
      border-radius:8px;letter-spacing:1px;}}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="logo">SENTINEL</div>
    <div class="sub">WEATHER &amp; RISK INTELLIGENCE PLATFORM</div>
  </div>
  <div class="body">
    <div style="background:{banner_bg};border:1px solid {color}44;border-left:4px solid {color};
                border-radius:8px;padding:16px;margin-bottom:24px;">
      <div style="font-size:18px;font-weight:700;color:{color};margin:0 0 4px;">&#9888; {level} RISK ALERT</div>
      <div style="font-size:13px;color:#94a3b8;">Risk threshold exceeded for {city}</div>
    </div>

    <div style="text-align:center;padding:24px 0;">
      <div style="font-family:monospace;font-size:56px;font-weight:700;color:{color};line-height:1;">{score}</div>
      <div style="font-size:12px;letter-spacing:2px;color:#4b6070;margin-top:4px;">RISK SCORE / 100</div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:20px 0;">
      <div class="stat"><div class="stat-label">CITY</div><div class="stat-value">{city}</div></div>
      <div class="stat"><div class="stat-label">CONDITION</div><div class="stat-value" style="font-size:14px;">{desc}</div></div>
      <div class="stat"><div class="stat-label">TEMPERATURE</div><div class="stat-value">{temp} C</div></div>
      <div class="stat"><div class="stat-label">FEELS LIKE</div><div class="stat-value">{feels} C</div></div>
      <div class="stat"><div class="stat-label">HUMIDITY</div><div class="stat-value">{humidity}%</div></div>
      <div class="stat"><div class="stat-label">WIND SPEED</div><div class="stat-value">{wind} km/h</div></div>
      <div class="stat"><div class="stat-label">PRESSURE</div><div class="stat-value">{pressure} hPa</div></div>
      <div class="stat"><div class="stat-label">VISIBILITY</div><div class="stat-value">{visibility} km</div></div>
    </div>

    <p style="font-size:13px;color:#94a3b8;margin:0 0 12px;">{risk_desc}</p>
    <div>{factors_html}</div>

    <div style="text-align:center;padding:20px 0 0;border-top:1px solid #1e2d3d;margin-top:24px;">
      <p style="font-size:11px;color:#4b6070;margin:2px 0;font-family:monospace;">Alert sent to: {user_email}</p>
      <p style="font-size:11px;color:#4b6070;margin:2px 0;font-family:monospace;">Threshold: {user_threshold} | Time: {timestamp}</p>
      <a href="http://localhost:5000" class="btn">VIEW DASHBOARD</a>
      <p style="margin-top:12px;font-size:11px;color:#4b6070;">To change alert settings, visit your Profile page.</p>
    </div>
  </div>
</div>
</body>
</html>"""
    return html, level, city, score


def send_risk_alert(user, weather_data, risk_data, app):
    from datetime import datetime
    timestamp     = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_email    = user.email
    user_threshold = user.alert_threshold

    html_body, level, city, score = _build_email(
        user_email, user_threshold, weather_data, risk_data, timestamp
    )
    subject = f'SENTINEL ALERT: {level} Risk Detected in {city}'

    def _send():
        print(f"\n{'='*55}")
        print(f"  SENTINEL ALERT FIRED")
        print(f"  To:        {user_email}")
        print(f"  City:      {city}")
        print(f"  Score:     {score}  |  Level: {level}")
        print(f"  Threshold: {user_threshold}")
        print(f"  Time:      {timestamp}")
        print(f"{'='*55}\n")

        try:
            with app.app_context():
                msg = Message(subject=subject, recipients=[user_email], html=html_body)
                mail.send(msg)
                print(f"  Email delivered to {user_email}\n")
        except Exception as e:
            print(f"  Email not sent (configure SMTP in .env to enable): {e}\n")

    threading.Thread(target=_send, daemon=True).start()


def check_and_alert(user, weather_data, risk_data, app):
    if not user.email_alerts:
        return False
    if risk_data.get('score', 0) >= user.alert_threshold:
        send_risk_alert(user, weather_data, risk_data, app)
        return True
    return False