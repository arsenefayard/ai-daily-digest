"""
Script d'envoi de l'email combiné — tous les digests
"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

_MONTHS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)


def send_combined_email():
    sender   = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')
    repo     = os.environ.get('GITHUB_REPO', '')
    if not all([sender, password, receiver]):
        print("❌ Variables email manquantes"); return False

    username = repo.split('/')[0] if '/' in repo else ''
    reponame = repo.split('/')[1] if '/' in repo else ''
    base = f"https://{username}.github.io/{reponame}"
    now = datetime.now()
    date_str = now.strftime('%d/%m/%Y')
    date_header = f"{now.day} {_MONTHS_FR[now.month - 1]} {now.year}"
    year = now.year

    html = f"""
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#1a1a1a;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#1a1a1a;">
<tr><td align="center" style="padding:30px 16px;">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="background:#222222;max-width:560px;">

  <!-- HEADER -->
  <tr>
    <td style="background:#1a1a1a;padding:26px 30px 20px;border-bottom:1px solid #2a2a2a;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td>
            <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#555;font-family:Arial,sans-serif;margin-bottom:8px;">{date_header} · Édition matinale</div>
            <div style="font-size:32px;font-weight:700;color:#f0ede6;line-height:1;font-family:Georgia,serif;">DAILY<br>BRIEFING</div>
            <div style="margin-top:14px;height:2px;width:40px;background:#c8a96e;"></div>
          </td>
          <td align="right" valign="top">
            <div style="font-size:9px;letter-spacing:2px;color:#444;font-family:Arial,sans-serif;">VOL. 01</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SPACER -->
  <tr><td style="height:2px;background:#111;"></td></tr>

  <!-- LIGNE 1 : IA + GEO -->
  <tr>
    <td style="padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="50%" style="background:#2d3d2e;padding:22px 20px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#5aaa72;font-family:Arial,sans-serif;margin-bottom:10px;">Intelligence Artificielle</div>
            <div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Modèles, régulation<br>et entreprises tech</div>
            <div style="margin-top:14px;"><a href="{base}/" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#5aaa72;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
          <td width="2" style="background:#111;"></td>
          <td width="50%" style="background:#1e2a38;padding:22px 20px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#4a88c0;font-family:Arial,sans-serif;margin-bottom:10px;">Géopolitique</div>
            <div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Conflits, diplomatie<br>et élections mondiales</div>
            <div style="margin-top:14px;"><a href="{base}/geo.html" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#4a88c0;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SPACER -->
  <tr><td style="height:2px;background:#111;"></td></tr>

  <!-- LIGNE 2 : ECO + SPORT -->
  <tr>
    <td style="padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="50%" style="background:#382a1a;padding:22px 20px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#c8862a;font-family:Arial,sans-serif;margin-bottom:10px;">Économie &amp; Finance</div>
            <div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Marchés, banques<br>et crypto</div>
            <div style="margin-top:14px;"><a href="{base}/eco.html" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c8862a;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
          <td width="2" style="background:#111;"></td>
          <td width="50%" style="background:#38201e;padding:22px 20px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#c84a4a;font-family:Arial,sans-serif;margin-bottom:10px;">Sport</div>
            <div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Football, tennis,<br>F1 &amp; NBA</div>
            <div style="margin-top:14px;"><a href="{base}/sport.html" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c84a4a;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SPACER -->
  <tr><td style="height:2px;background:#111;"></td></tr>

  <!-- LIGNE 3 : MUSIQUE + SCIENCES + CULTURE -->
  <tr>
    <td style="padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="33%" style="background:#261e38;padding:18px 16px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#7a5cc8;font-family:Arial,sans-serif;margin-bottom:8px;">Musique</div>
            <div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Métal, rock<br>&amp; industrie</div>
            <div style="margin-top:12px;"><a href="{base}/music.html" style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#7a5cc8;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
          <td width="1" style="background:#111;"></td>
          <td width="33%" style="background:#1a2e28;padding:18px 16px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#2a9e7a;font-family:Arial,sans-serif;margin-bottom:8px;">Sciences</div>
            <div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Physique, espace<br>&amp; médecine</div>
            <div style="margin-top:12px;"><a href="{base}/science.html" style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#2a9e7a;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
          <td width="1" style="background:#111;"></td>
          <td width="33%" style="background:#2e1a28;padding:18px 16px;vertical-align:top;">
            <div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#c84a8a;font-family:Arial,sans-serif;margin-bottom:8px;">Culture</div>
            <div style="font-size:12px;font-weight:700;color:#f0ede6;line-height:1.3;font-family:Georgia,serif;">Philo, cinéma<br>&amp; insolite</div>
            <div style="margin-top:12px;"><a href="{base}/culture.html" style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#c84a8a;font-family:Arial,sans-serif;text-decoration:none;">Lire →</a></div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SPACER -->
  <tr><td style="height:2px;background:#111;"></td></tr>

  <!-- HISTOIRE pleine largeur -->
  <tr>
    <td style="background:#2a2010;padding:18px 22px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="4" style="background:#a07840;vertical-align:top;padding-right:14px;"></td>
          <td style="padding-left:14px;">
            <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#a07840;font-family:Arial,sans-serif;margin-bottom:6px;">Histoire</div>
            <div style="font-size:14px;font-weight:700;color:#f0ede6;font-family:Georgia,serif;">Antiquité, guerres &amp; civilisations</div>
          </td>
          <td align="right" valign="middle">
            <a href="{base}/history.html" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#a07840;font-family:Arial,sans-serif;text-decoration:none;white-space:nowrap;">Lire →</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SPACER -->
  <tr><td style="height:2px;background:#111;"></td></tr>

  <!-- FAVORIS -->
  <tr>
    <td style="background:#1e1c10;padding:14px 22px;border-top:1px solid #2a2418;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td>
            <span style="font-size:13px;color:#c8a96e;">★</span>
            <span style="font-size:9px;letter-spacing:2.5px;text-transform:uppercase;color:#c8a96e;font-family:Arial,sans-serif;font-weight:700;margin-left:10px;">Mes Favoris</span>
          </td>
          <td align="right">
            <a href="{base}/favorites.html" style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#554f3a;font-family:Arial,sans-serif;text-decoration:none;">Retrouver →</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#111;padding:12px 24px;border-top:1px solid #1e1e1e;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">Diffusion restreinte · Usage professionnel</td>
          <td align="right" style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">{year}</td>
        </tr>
      </table>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

    recipients = [r.strip() for r in receiver.split(',') if r.strip()]
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"Daily Briefing — {date_str}"
        msg['From']    = sender
        msg['To']      = ', '.join(recipients)
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        print(f"✅ Email combiné envoyé à {len(recipients)} destinataire(s) !")
        return True
    except Exception as e:
        print(f"❌ Erreur : {e}"); return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if send_combined_email() else 1)
