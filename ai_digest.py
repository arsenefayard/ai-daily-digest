"""
Script de digest quotidien IA avec Perplexity API
Génère un fichier JSON sur GitHub Pages et envoie un lien par email.

INSTRUCTIONS :
1. pip install requests
2. Variables GitHub Actions à configurer :
   PERPLEXITY_API_KEY, SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL
   GITHUB_TOKEN (déjà disponible automatiquement dans GitHub Actions)
   GITHUB_REPO (ex: tonusername/tonrepo)
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import base64


def get_ai_news_summaries():
    """Utilise Perplexity pour rechercher et résumer les actualités IA du jour en JSON"""

    api_key = os.environ.get('PERPLEXITY_API_KEY')

    if not api_key:
        print("❌ Erreur : PERPLEXITY_API_KEY non trouvée")
        return None

    print("🔍 Recherche des actualités IA avec Perplexity...")

    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": """Tu es un assistant spécialisé dans les actualités IA.

Recherche sur le web les 5 actualités IA les plus importantes publiées aujourd'hui ou dans les derniers jours.

Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte Markdown, sans ``` et sans préambule.

Format JSON strict :
{
  "date": "JJ/MM/AAAA",
  "news": [
    {
      "title": "Titre de l'actualité",
      "summary": "Résumé détaillé en 5-6 phrases avec contexte, détails techniques et implications concrètes.",
      "why": "Pourquoi c'est important en 1-2 phrases.",
      "category": "Modèle|Entreprise|Recherche|Application|Régulation"
    }
  ]
}

Génère exactement 5 objets dans "news".
Concentre-toi sur : nouveaux modèles IA, annonces d'entreprises tech, avancées scientifiques, applications pratiques, régulations.
Réponds UNIQUEMENT avec le JSON, rien d'autre."""
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
        raw = result['choices'][0]['message']['content']

        # Nettoyage au cas où Perplexity ajouterait des backticks
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()

        data = json.loads(raw)
        print("✅ Résumés générés avec succès")
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API Perplexity : {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur parsing JSON : {e}")
        print(f"Contenu reçu : {raw}")
        return None


def ensure_gh_pages_branch(repo, headers):
    """Crée la branche gh-pages si elle n'existe pas encore"""

    # Récupère le SHA du dernier commit de main
    r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/main", headers=headers)
    if r.status_code != 200:
        # Essaie master si main n'existe pas
        r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/master", headers=headers)
    if r.status_code != 200:
        print("❌ Impossible de trouver la branche principale (main/master)")
        return False

    sha = r.json()["object"]["sha"]

    # Crée gh-pages à partir de ce SHA
    payload = {"ref": "refs/heads/gh-pages", "sha": sha}
    r = requests.post(f"https://api.github.com/repos/{repo}/git/refs", json=payload, headers=headers)
    if r.status_code in (201, 422):  # 422 = existe déjà, ok
        print("✅ Branche gh-pages créée")
        return True

    print(f"❌ Erreur création gh-pages : {r.text}")
    return False


def push_file_to_gh_pages(repo, headers, filename, content_str, commit_message):
    """Pousse un fichier sur la branche gh-pages"""

    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    # Récupère le SHA existant si le fichier existe déjà
    sha = None
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        sha = r.json().get("sha")

    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": "gh-pages"
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, json=payload, headers=headers)
    r.raise_for_status()


def push_json_to_github(data):
    """Pousse today.json et index.html sur la branche gh-pages"""

    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPO')

    if not token or not repo:
        print("❌ GITHUB_TOKEN ou GITHUB_REPO manquant")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    # Crée gh-pages si elle n'existe pas
    ensure_gh_pages_branch(repo, headers)

    date_str = data.get('date', datetime.now().strftime('%d/%m/%Y'))

    try:
        # 1. Pousse today.json
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        push_file_to_gh_pages(repo, headers, "today.json", json_content, f"digest: {date_str}")
        print("✅ today.json publié sur gh-pages")

        # 2. Pousse index.html s'il existe dans le répertoire courant
        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            push_file_to_gh_pages(repo, headers, "index.html", html_content, "chore: update index.html")
            print("✅ index.html publié sur gh-pages")

        return True

    except Exception as e:
        print(f"❌ Erreur push GitHub : {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails : {e.response.text}")
        return False


def send_email(date_str, page_url):
    """Envoie un email minimaliste avec le lien vers la page du jour"""

    sender = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')

    if not all([sender, password, receiver]):
        print("❌ Variables d'environnement email manquantes")
        return False

    print(f"📧 Envoi de l'email à {receiver}...")

    html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Georgia, serif; background: #f4f4f0; margin: 0; padding: 40px 20px;">
      <div style="max-width: 480px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <p style="color: #999; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 16px;">AI Digest · {date_str}</p>
        <h1 style="font-size: 26px; color: #111; margin: 0 0 16px; line-height: 1.3;">Vos 5 actualités IA du jour sont prêtes</h1>
        <p style="color: #555; font-size: 15px; line-height: 1.7; margin: 0 0 32px;">Swipez pour découvrir les nouvelles les plus importantes dans le monde de l'intelligence artificielle.</p>
        <a href="{page_url}" style="display: inline-block; background: #111; color: white; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 15px; font-weight: 500; letter-spacing: 0.5px;">
          Ouvrir le digest →
        </a>
        <p style="color: #bbb; font-size: 12px; margin: 32px 0 0;">Généré automatiquement · Perplexity AI</p>
      </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"🤖 Digest IA — {date_str}"
        msg['From'] = sender
        msg['To'] = receiver
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        print("✅ Email envoyé avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False


def main():
    print("\n" + "="*50)
    print("🤖 AI DAILY DIGEST — Démarrage")
    print("="*50 + "\n")

    # 1. Génère les news en JSON
    data = get_ai_news_summaries()
    if not data:
        print("❌ Impossible de générer les résumés")
        return

    # 2. Pousse sur GitHub Pages
    pushed = push_json_to_github(data)
    if not pushed:
        print("⚠️  Données générées mais non publiées sur GitHub Pages")

    # 3. Construit l'URL de la page
    repo = os.environ.get('GITHUB_REPO', '')
    username = repo.split('/')[0] if '/' in repo else ''
    reponame = repo.split('/')[1] if '/' in repo else ''
    page_url = f"https://{username}.github.io/{reponame}/"

    # 4. Envoie l'email avec le lien
    date_str = data.get('date', datetime.now().strftime('%d/%m/%Y'))
    send_email(date_str, page_url)

    print("\n✅ Processus terminé !")


if __name__ == "__main__":
    main()
