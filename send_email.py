"""
Script d'envoi de l'email combiné — tous les digests
"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

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
    date_str = datetime.now().strftime('%d/%m/%Y')

    html = f"""
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:40px 20px;background:#1a1a1a;font-family:Georgia,serif;">
<div style="max-width:560px;margin:0 auto;background:#111111;border:0.5px solid #2a2a2a;">

  <!-- Header -->
  <div style="background:#0a0a0a;padding:22px 32px;border-bottom:0.5px solid #2a2a2a;">
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:2px;height:34px;background:#c8a96e;flex-shrink:0;"></div>
        <div>
          <div style="font-size:16px;font-weight:500;color:#f0ede6;letter-spacing:0.3px;font-family:Georgia,serif;">Daily Briefing</div>
          <div style="font-size:9px;letter-spacing:2.5px;text-transform:uppercase;color:#555;font-family:Arial,sans-serif;margin-top:3px;">Veille Stratégique</div>
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:11px;color:#c8a96e;font-family:Georgia,serif;font-style:italic;">{date_str}</div>
        <div style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:#444;font-family:Arial,sans-serif;margin-top:3px;">Édition matinale</div>
      </div>
    </div>
  </div>

  <!-- Ligne dorée -->
  <div style="height:1px;background:#c8a96e;opacity:0.25;"></div>

  <!-- Grille 2 colonnes -->
  <div style="padding:16px 16px 12px;display:grid;grid-template-columns:1fr 1fr;gap:7px;">

    <a href="{base}/" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#5aaa72;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Intelligence Artificielle</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/geo.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#4a88c0;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Géopolitique</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/eco.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#c8862a;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Économie & Finance</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/sport.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#c84a4a;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Sport</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/music.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#7a5cc8;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Musique</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/science.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#2a9e7a;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Sciences</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/culture.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#c84a8a;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Culture Générale</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

    <a href="{base}/history.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;border:0.5px solid #222;padding:13px 14px;background:#161616;">
      <div style="width:2px;height:22px;background:#a07840;flex-shrink:0;"></div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#b8b5ae;font-family:Arial,sans-serif;font-weight:500;flex:1;">Histoire</div>
      <div style="font-size:10px;color:#3a3a3a;font-family:Arial,sans-serif;">→</div>
    </a>

  </div>

  <!-- Favoris -->
  <div style="margin:0 16px 16px;padding-top:8px;border-top:0.5px solid #1e1e1e;">
    <a href="{base}/favorites.html" style="text-decoration:none;display:flex;align-items:center;gap:12px;padding:11px 14px;border:0.5px solid #2a2418;background:#131108;">
      <div style="font-size:12px;color:#c8a96e;flex-shrink:0;">★</div>
      <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#c8a96e;font-family:Arial,sans-serif;font-weight:500;flex:1;">Mes Favoris</div>
      <div style="font-size:10px;color:#554f3a;font-family:Arial,sans-serif;">→</div>
    </a>
  </div>

  <!-- Footer -->
  <div style="background:#0a0a0a;border-top:0.5px solid #1e1e1e;padding:13px 32px;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:9px;color:#333;font-family:Arial,sans-serif;letter-spacing:1px;text-transform:uppercase;">Diffusion restreinte · Usage professionnel</div>
    <div style="font-size:9px;color:#333;font-family:Arial,sans-serif;letter-spacing:1px;text-transform:uppercase;">Daily Briefing</div>
  </div>

</div>
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
