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

    digests = [
        {"label": "IA",           "emoji": "🤖", "url": f"{base}/",                "accent": "#c8f064", "bg": "#0d1117"},
        {"label": "Géopolitique", "emoji": "🌍", "url": f"{base}/geo.html",        "accent": "#60c8f0", "bg": "#080d11"},
        {"label": "Économie",     "emoji": "💰", "url": f"{base}/eco.html",        "accent": "#f59e0b", "bg": "#0d0a00"},
        {"label": "Sport",        "emoji": "⚽", "url": f"{base}/sport.html",      "accent": "#f87171", "bg": "#0d0606"},
        {"label": "Musique",      "emoji": "🎸", "url": f"{base}/music.html",      "accent": "#a78bfa", "bg": "#08060d"},
        {"label": "Science",      "emoji": "🔬", "url": f"{base}/science.html",    "accent": "#34d399", "bg": "#040d09"},
        {"label": "Culture",      "emoji": "🎲", "url": f"{base}/culture.html",    "accent": "#f472b6", "bg": "#0d0609"},
        {"label": "Histoire",     "emoji": "📜", "url": f"{base}/history.html",    "accent": "#e8b86d", "bg": "#0d0900"},
    ]

    # Build 2-column grid
    rows = ""
    for i in range(0, len(digests), 2):
        pair = digests[i:i+2]
        cells = ""
        for d in pair:
            cells += f"""
            <td style="width:50%;padding:6px;vertical-align:top;">
              <a href="{d['url']}" style="display:block;text-decoration:none;background:{d['bg']};border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:18px 16px;transition:opacity .2s;">
                <div style="font-size:22px;margin-bottom:8px;">{d['emoji']}</div>
                <div style="color:{d['accent']};font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;margin-bottom:6px;">{d['label']}</div>
                <div style="color:rgba(232,228,220,0.4);font-size:11px;font-family:monospace;">5 infos →</div>
              </a>
            </td>"""
        # pad last row if odd
        if len(pair) == 1:
            cells += "<td style='width:50%;padding:6px;'></td>"
        rows += f"<tr>{cells}</tr>"

    fav_section = f"""
<div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);">
  <a href="{base}/favorites.html" style="display:block;text-decoration:none;background:#0d0d0d;border:1px solid rgba(251,191,36,0.2);border-radius:12px;padding:16px 20px;text-align:center;">
    <span style="font-size:20px;">⭐</span>
    <div style="color:#fbbf24;font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;margin-top:6px;">Mes Favoris</div>
  </a>
</div>
"""

    html = f"""
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Georgia,serif;background:#000000;margin:0;padding:30px 16px;">
      <div style="max-width:480px;margin:0 auto;">
        <p style="color:#555;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin:0 0 6px;text-align:center;font-family:monospace;">Daily Digest</p>
        <p style="color:#333;font-size:11px;text-align:center;margin:0 0 24px;font-family:monospace;">{date_str}</p>
        <table style="width:100%;border-collapse:collapse;">
          {rows}
        </table>
        {fav_section}
        <p style="color:#333;font-size:10px;text-align:center;margin:20px 0 0;font-family:monospace;">Généré automatiquement · Perplexity AI</p>
      </div>
    </body></html>
    """

    recipients = [r.strip() for r in receiver.split(',') if r.strip()]
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"📰 Daily Digest — {date_str}"
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
