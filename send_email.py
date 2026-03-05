"""
Script d'envoi de l'email combiné IA + Géopolitique
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_combined_email():
    sender   = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')
    repo     = os.environ.get('GITHUB_REPO', '')

    if not all([sender, password, receiver]):
        print("❌ Variables d'environnement email manquantes")
        return False

    username = repo.split('/')[0] if '/' in repo else ''
    reponame = repo.split('/')[1] if '/' in repo else ''
    base_url = f"https://{username}.github.io/{reponame}"

    ai_url  = f"{base_url}/"
    geo_url = f"{base_url}/geo.html"
    date_str = datetime.now().strftime('%d/%m/%Y')

    print(f"📧 Envoi de l'email combiné à {receiver}...")

    html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Georgia, serif; background: #f4f4f0; margin: 0; padding: 40px 20px;">
      <div style="max-width: 520px; margin: 0 auto;">

        <p style="color: #999; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 24px; text-align:center;">
          Daily Digest · {date_str}
        </p>

        <!-- IA -->
        <div style="background: #0d1117; border-radius: 14px; padding: 28px 32px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.06);">
          <p style="color: #c8f064; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 10px; font-family: monospace;">Intelligence Artificielle</p>
          <h2 style="font-size: 20px; color: #e8e4dc; margin: 0 0 10px; line-height: 1.3; font-family: Georgia, serif;">5 actualités IA du jour</h2>
          <p style="color: rgba(232,228,220,0.5); font-size: 13px; margin: 0 0 20px; line-height: 1.6;">Modèles, entreprises, recherche et régulation.</p>
          <a href="{ai_url}" style="display:inline-block; background:#c8f064; color:#06080d; text-decoration:none; padding:11px 22px; border-radius:8px; font-size:13px; font-weight:600; letter-spacing:0.5px;">
            Ouvrir →
          </a>
        </div>

        <!-- Géopolitique -->
        <div style="background: #080d11; border-radius: 14px; padding: 28px 32px; margin-bottom: 24px; border: 1px solid rgba(255,255,255,0.06);">
          <p style="color: #60c8f0; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 10px; font-family: monospace;">Géopolitique Mondiale</p>
          <h2 style="font-size: 20px; color: #e8e4dc; margin: 0 0 10px; line-height: 1.3; font-family: Georgia, serif;">5 actualités géopolitiques du jour</h2>
          <p style="color: rgba(232,228,220,0.5); font-size: 13px; margin: 0 0 20px; line-height: 1.6;">Conflits, diplomatie, élections et économie mondiale.</p>
          <a href="{geo_url}" style="display:inline-block; background:#60c8f0; color:#06080d; text-decoration:none; padding:11px 22px; border-radius:8px; font-size:13px; font-weight:600; letter-spacing:0.5px;">
            Ouvrir →
          </a>
        </div>

        <p style="color: #bbb; font-size: 11px; text-align:center; margin:0;">Généré automatiquement · Perplexity AI</p>
      </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"📰 Daily Digest — {date_str}"
        msg['From']    = sender
        msg['To']      = receiver
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("✅ Email combiné envoyé !")
        return True
    except Exception as e:
        print(f"❌ Erreur envoi : {e}")
        return False


if __name__ == "__main__":
    send_combined_email()
