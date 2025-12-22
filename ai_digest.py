"""
Script de digest quotidien IA avec Perplexity API

INSTRUCTIONS :
1. pip install requests
2. Crée un fichier .env avec :
   PERPLEXITY_API_KEY=ta_clé_ici
   SENDER_EMAIL=ton_email@gmail.com
   EMAIL_PASSWORD=ton_mot_de_passe_application_gmail
   RECEIVER_EMAIL=email_destination@gmail.com
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def get_ai_news_summaries():
    """Utilise Perplexity pour rechercher et résumer les actualités IA du jour"""
    
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    
    if not api_key:
        print("❌ Erreur : PERPLEXITY_API_KEY non trouvée")
        print("💡 Crée un fichier .env avec : PERPLEXITY_API_KEY=ta_clé")
        return None
    
    print("🔍 Recherche des actualités IA avec Perplexity...")
    
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",  # Modèle avec recherche web
        "messages": [
            {
                "role": "system",
                "content": """Tu es un assistant spécialisé dans les actualités IA.
                
Recherche sur le web les 5 actualités les plus importantes et récentes (dernières 48h) sur l'intelligence artificielle.

Pour chacune, fournis :
1. Un titre clair
2. Un résumé de 3-4 phrases en français
3. Pourquoi c'est important

Formate comme ça :

## 1. [TITRE]

Résumé : [résumé détaillé]

Pourquoi c'est important : [explication]

---

Concentre-toi sur : nouveaux modèles, annonces d'entreprises, avancées scientifiques, applications pratiques, régulations."""
            },
            {
                "role": "user",
                "content": f"Quelles sont les 5 actualités IA les plus importantes des dernières 48 heures ? Date : {datetime.now().strftime('%d/%m/%Y')}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        summaries = result['choices'][0]['message']['content']
        
        print("✅ Résumés générés avec succès")
        return summaries
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API Perplexity : {e}")
        if hasattr(e.response, 'text'):
            print(f"Détails : {e.response.text}")
        return None


def create_email_body(summaries):
    """Crée le corps de l'email avec mise en forme HTML"""
    
    # Nettoie les résumés en retirant les ** et "Résumé :" / "Pourquoi c'est important :"
    cleaned = summaries.replace('**', '')
    cleaned = cleaned.replace('Résumé : ', '')
    cleaned = cleaned.replace('Pourquoi c\'est important : ', '💡 ')
    
    # Convertit en HTML pour une meilleure mise en forme
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h2 {{
                color: #2563eb;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 10px;
                margin-top: 30px;
            }}
            h3 {{
                color: #1e40af;
                margin-top: 25px;
            }}
            .lightbulb {{
                color: #059669;
                font-weight: 500;
            }}
            hr {{
                border: none;
                border-top: 1px solid #e5e7eb;
                margin: 25px 0;
            }}
        </style>
    </head>
    <body>
        <h2>🤖 Votre digest IA quotidien - {datetime.now().strftime('%d/%m/%Y')}</h2>
        <p>Voici les 5 actualités IA les plus importantes du jour :</p>
        
        {cleaned.replace('## ', '<h3>').replace('---', '<hr>')}
        
        <hr>
        <p style="color: #6b7280; font-size: 0.9em;">
            Bonne journée !<br>
            <em>Généré automatiquement par Perplexity AI</em>
        </p>
    </body>
    </html>
    """
    
    return html


def send_email(body):
    """Envoie l'email via Gmail"""
    
    sender = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')
    
    if not all([sender, password, receiver]):
        print("❌ Erreur : Variables d'environnement email manquantes")
        return False
    
    print(f"📧 Envoi de l'email à {receiver}...")
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"🤖 Digest IA du {datetime.now().strftime('%d/%m/%Y')}"
        msg['From'] = sender
        msg['To'] = receiver
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        
        print("✅ Email envoyé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False


def main():
    """Fonction principale"""
    
    print("\n" + "="*50)
    print("🤖 AI DAILY DIGEST - Démarrage")
    print("="*50 + "\n")
    
    # Récupère les résumés avec Perplexity
    summaries = get_ai_news_summaries()
    
    if not summaries:
        print("\n❌ Impossible de générer les résumés")
        return
    
    # Affiche les résumés
    print("\n" + "="*50)
    print("📰 RÉSUMÉS GÉNÉRÉS :")
    print("="*50 + "\n")
    print(summaries)
    print("\n" + "="*50 + "\n")
    
    # Crée et envoie l'email
    email_body = create_email_body(summaries)
    success = send_email(email_body)
    
    if success:
        print("\n✅ Processus terminé avec succès !")
    else:
        print("\n⚠️ Résumés générés mais email non envoyé")


if __name__ == "__main__":
    main()
