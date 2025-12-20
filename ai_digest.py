"""
Script de digest quotidien IA avec OpenAI GPT-4o-mini

INSTRUCTIONS POUR CURSOR :

1. Installe les dépendances : pip install openai

2. Crée un fichier .env avec :

   OPENAI_API_KEY=ta_clé_ici

   SENDER_EMAIL=ton_email@gmail.com

   EMAIL_PASSWORD=ton_mot_de_passe_application_gmail

   RECEIVER_EMAIL=email_destination@gmail.com

3. Lance le script : python ai_digest.py

"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from openai import OpenAI


def get_ai_news_summaries():
    """Utilise OpenAI pour rechercher et résumer les actualités IA du jour"""

    api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        print("❌ Erreur : OPENAI_API_KEY non trouvée")
        print("💡 Crée un fichier .env avec : OPENAI_API_KEY=ta_clé")
        return None

    print("🔍 Recherche des actualités IA en cours...")

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system',
                    'content': '''Tu es un assistant spécialisé dans les actualités IA.

Trouve les 5 actualités les plus importantes et récentes sur l'intelligence artificielle.
Pour chacune, fournis :

1. Un titre clair
2. Un résumé de 3-4 phrases en français
3. Pourquoi c'est important

Formate comme ça :

## 1. [TITRE]

Résumé : [ton résumé]

Pourquoi c'est important : [explication]

---

Répète pour les 5 actualités.'''
                },
                {
                    'role': 'user',
                    'content': f"Quelles sont les 5 actualités IA les plus importantes récentes ? Date du jour : {datetime.now().strftime('%d/%m/%Y')}"
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        summaries = response.choices[0].message.content
        print("✅ Résumés générés avec succès")
        return summaries

    except Exception as e:
        print(f"❌ Erreur API OpenAI : {e}")
        return None


def create_email_body(summaries):
    """Crée le corps de l'email"""

    body = f"""Bonjour,

Voici votre digest IA quotidien du {datetime.now().strftime('%d/%m/%Y')} 🤖

{summaries}

---

Bonne journée !

"""
    return body


def send_email(body):
    """Envoie l'email via Gmail"""

    sender = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')

    if not all([sender, password, receiver]):
        print("❌ Erreur : Variables d'environnement email manquantes")
        print("💡 Ajoute dans .env : SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL")
        return False

    print(f"📧 Envoi de l'email à {receiver}...")

    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"🤖 Digest IA du {datetime.now().strftime('%d/%m/%Y')}"
        msg['From'] = sender
        msg['To'] = receiver

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

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

    # Récupère les résumés
    summaries = get_ai_news_summaries()

    if not summaries:
        print("\n❌ Impossible de générer les résumés")
        return

    # Affiche les résumés dans le terminal
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
        print("💡 Vérifie tes paramètres Gmail")


if __name__ == "__main__":
    main()

