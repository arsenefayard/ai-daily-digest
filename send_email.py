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
        {"label": "Intelligence Artificielle", "url": f"{base}/",            "accent": "#c8f064", "bg": "#06080d", "desc": "Modèles, entreprises, recherche et régulation."},
        {"label": "Géopolitique Mondiale",      "url": f"{base}/geo.html",    "accent": "#60c8f0", "bg": "#06080d", "desc": "Conflits, diplomatie, élections et économie mondiale."},
        {"label": "Économie & Finance",         "url": f"{base}/eco.html",    "accent": "#f59e0b", "bg": "#0d0a00", "desc": "Marchés, banques centrales, crypto et entreprises."},
        {"label": "Sport Mondial",              "url": f"{base}/sport.html",  "accent": "#f87171", "bg": "#0d0606", "desc": "Football, tennis, NBA, F1 et bien plus."},
        {"label": "Musique & Métal",            "url": f"{base}/music.html",  "accent": "#a78bfa", "bg": "#08060d", "desc": "Métal, rock, sorties d'albums et actu musicale."},
        {"label": "Sciences",                   "url": f"{base}/science.html","accent": "#34d399", "bg": "#040d09", "desc": "Physique, chimie, espace, médecine et maths."},
        {"label": "Culture Générale",           "url": f"{base}/culture.html","accent": "#f472b6", "bg": "#0d0609", "desc": "Insolite, philosophie, cinéma, histoire et société."},
    ]

    cards = ""
    for d in digests:
        cards += f"""
        <div style="background:{d['bg']};border-radius:12px;padding:22px 26px;margin-bottom:12px;border:1px solid rgba(255,255,255,0.06);">
          <p style="color:{d['accent']};font-size:10px;letter-spacing:2px;text-transform:uppercase;margin:0 0 8px;font-family:monospace;">{d['label']}</p>
          <p style="color:rgba(232,228,220,0.5);font-size:12px;margin:0 0 16px;line-height:1.5;">{d['desc']}</p>
          <a href="{d['url']}" style="display:inline-block;background:{d['accent']};color:#06080d;text-decoration:none;padding:9px 18px;border-radius:7px;font-size:12px;font-weight:700;letter-spacing:0.5px;">Ouvrir →</a>
        </div>"""

    html = f"""
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Georgia,serif;background:#f0f0ec;margin:0;padding:30px 16px;">
      <div style="max-width:500px;margin:0 auto;">
        <p style="color:#999;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin:0 0 20px;text-align:center;">Daily Digest · {date_str}</p>
        {cards}
        <p style="color:#bbb;font-size:11px;text-align:center;margin:16px 0 0;">Généré automatiquement · Perplexity AI</p>
      </div>
    </body></html>
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
        print(f"❌ Erreur : {e}"); return False

if __name__ == "__main__":
    send_combined_email()
