"""
Script d'envoi de l'email combinÃ© â€” tous les digests
"""
import html
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

_MONTHS_FR = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)


def _clean_line(text, fallback):
    t = " ".join(str(text or "").split()).strip()
    if not t:
        t = fallback
    return html.escape(t[:96])


def _fetch_digest_line(base, path, fallback):
    try:
        r = requests.get(f"{base}/{path}", timeout=8)
        if not r.ok:
            return html.escape(fallback)
        data = r.json()
        if isinstance(data, dict):
            news = data.get("news")
            if isinstance(news, list) and news and news[0].get("title"):
                return _clean_line(news[0]["title"], fallback)
            updates = data.get("updates")
            if isinstance(updates, list) and updates and updates[0].get("title"):
                return _clean_line(updates[0]["title"], fallback)
            subject = data.get("subject")
            if isinstance(subject, dict) and subject.get("name"):
                return _clean_line(subject["name"], fallback)
    except Exception:
        pass
    return html.escape(fallback)


def send_combined_email():
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("RECEIVER_EMAIL")
    repo = os.environ.get("GITHUB_REPO", "")
    if not all([sender, password, receiver]):
        print("âŒ Variables email manquantes")
        return False

    username = repo.split("/")[0] if "/" in repo else ""
    reponame = repo.split("/")[1] if "/" in repo else ""
    base = f"https://{username}.github.io/{reponame}"
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    date_header = f"{now.day} {_MONTHS_FR[now.month - 1]} {now.year}"
    year = now.year

    cap_ia = _fetch_digest_line(base, "today.json", "Actualites IA du jour")
    cap_geo = _fetch_digest_line(base, "geo_today.json", "Actualites geopolitique du jour")
    cap_eco = _fetch_digest_line(base, "eco_today.json", "Actualites economie du jour")
    cap_sport = _fetch_digest_line(base, "sport_today.json", "Actualites sport du jour")
    cap_music = _fetch_digest_line(base, "music_today.json", "Actualites musique du jour")
    cap_science = _fetch_digest_line(base, "science_today.json", "Actualites science du jour")
    cap_culture = _fetch_digest_line(base, "culture_today.json", "Actualites culture du jour")
    cap_history = _fetch_digest_line(base, "history_today.json", "Sujet d'histoire du jour")

    html = f"""
<html>
<head>
  <meta charset="UTF-8">
  <meta name="color-scheme" content="dark light">
  <meta name="supported-color-schemes" content="dark light">
  <style>
    :root {{ color-scheme: dark; supported-color-schemes: dark; }}
    @media (prefers-color-scheme: dark) {{
      body, table, td {{ background-color: #1a1a1a !important; color: #f0ede6 !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#1a1a1a;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#1a1a1a;">
<tr><td align="center" style="padding:30px 16px;">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="background:#222222;max-width:560px;">

  <tr>
    <td style="background:#1a1a1a;padding:26px 30px 20px;border-bottom:1px solid #2a2a2a;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td>
            <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#555;font-family:Arial,sans-serif;margin-bottom:8px;">{date_header} Â· Edition matinale</div>
            <div style="font-size:32px;font-weight:700;color:#f0ede6;line-height:1;font-family:Georgia,serif;">DAILY<br>BRIEFING</div>
            <div style="margin-top:14px;height:2px;width:40px;background:#c8a96e;"></div>
          </td>
          <td align="right" valign="top"><div style="font-size:9px;letter-spacing:2px;color:#444;font-family:Arial,sans-serif;">VOL. 01</div></td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="50%" style="background:#2d3d2e;padding:0;vertical-align:top;"><a href="{base}/" style="display:block;padding:22px 20px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#5aaa72;font-family:Arial,sans-serif;margin-bottom:10px;">Intelligence Artificielle</div><div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_ia}</div></a></td>
    <td width="2" style="background:#111;"></td>
    <td width="50%" style="background:#1e2a38;padding:0;vertical-align:top;"><a href="{base}/geo.html" style="display:block;padding:22px 20px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#4a88c0;font-family:Arial,sans-serif;margin-bottom:10px;">Geopolitique</div><div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_geo}</div></a></td>
  </tr></table></td></tr>

  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="50%" style="background:#382a1a;padding:0;vertical-align:top;"><a href="{base}/eco.html" style="display:block;padding:22px 20px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#c8862a;font-family:Arial,sans-serif;margin-bottom:10px;">Economie &amp; Finance</div><div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_eco}</div></a></td>
    <td width="2" style="background:#111;"></td>
    <td width="50%" style="background:#38201e;padding:0;vertical-align:top;"><a href="{base}/sport.html" style="display:block;padding:22px 20px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#c84a4a;font-family:Arial,sans-serif;margin-bottom:10px;">Sport</div><div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_sport}</div></a></td>
  </tr></table></td></tr>

  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="33%" style="background:#261e38;padding:0;vertical-align:top;"><a href="{base}/music.html" style="display:block;padding:18px 16px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#7a5cc8;font-family:Arial,sans-serif;margin-bottom:8px;">Musique</div><div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_music}</div></a></td>
    <td width="1" style="background:#111;"></td>
    <td width="33%" style="background:#1a2e28;padding:0;vertical-align:top;"><a href="{base}/science.html" style="display:block;padding:18px 16px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#2a9e7a;font-family:Arial,sans-serif;margin-bottom:8px;">Sciences</div><div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_science}</div></a></td>
    <td width="1" style="background:#111;"></td>
    <td width="33%" style="background:#2e1a28;padding:0;vertical-align:top;"><a href="{base}/culture.html" style="display:block;padding:18px 16px;text-decoration:none;color:inherit;"><div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#c84a8a;font-family:Arial,sans-serif;margin-bottom:8px;">Culture</div><div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">{cap_culture}</div></a></td>
  </tr></table></td></tr>

  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="background:#2a2010;padding:0;"><a href="{base}/history.html" style="display:block;padding:18px 22px;text-decoration:none;color:inherit;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td><div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#a07840;font-family:Arial,sans-serif;margin-bottom:6px;">Histoire</div><div style="font-size:14px;font-weight:700;color:#f0ede6;font-family:Georgia,serif;">{cap_history}</div></td></tr></table></a></td></tr>

  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="background:#1e1c10;padding:14px 22px;border-top:1px solid #2a2418;"><a href="{base}/favorites.html" style="display:block;text-decoration:none;color:inherit;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td><span style="font-size:13px;color:#c8a96e;">â˜…</span><span style="font-size:9px;letter-spacing:2.5px;text-transform:uppercase;color:#c8a96e;font-family:Arial,sans-serif;font-weight:700;margin-left:10px;">Mes Favoris</span></td><td align="right"><span style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#554f3a;font-family:Arial,sans-serif;">Retrouver â†’</span></td></tr></table></a></td></tr>

  <tr><td style="background:#111;padding:12px 24px;border-top:1px solid #1e1e1e;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">Diffusion restreinte Â· Usage professionnel</td><td align="right" style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">{year}</td></tr></table></td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

    recipients = [r.strip() for r in receiver.split(",") if r.strip()]
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Daily Briefing â€” {date_str}"
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        print(f"âœ… Email combinÃ© envoyÃ© Ã  {len(recipients)} destinataire(s) !")
        return True
    except Exception as e:
        print(f"âŒ Erreur : {e}")
        return False


if __name__ == "__main__":
    import sys

    sys.exit(0 if send_combined_email() else 1)
