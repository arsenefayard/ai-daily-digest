"""
Script de digest quotidien IA avec Perplexity API
Génère un fichier JSON sur GitHub Pages et envoie un lien par email.
"""

import os
import json
import re
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import base64


# ─────────────────────────────────────────
# HISTORIQUE
# ─────────────────────────────────────────

def fetch_history(repo, headers):
    """Récupère history.json depuis gh-pages (7 derniers jours de titres)"""
    api_url = f"https://api.github.com/repos/{repo}/contents/history.json"
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return json.loads(content)
    return []  # Pas encore d'historique


def update_history(history, new_news, updates=None):
    """Ajoute les titres du jour et garde seulement les 7 derniers jours"""
    titles = [item["title"] for item in new_news]
    if updates:
        titles += [item["title"] for item in updates]
    today = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "titles": titles
    }
    history.append(today)
    return history[-7:]  # Garde les 7 derniers jours


def build_history_context(history):
    """Formate l'historique en texte pour le prompt"""
    if not history:
        return ""
    lines = ["Actualités déjà couvertes ces derniers jours (à éviter sauf changement majeur) :"]
    for day in history:
        lines.append(f"\n{day['date']} :")
        for title in day["titles"]:
            lines.append(f"  - {title}")
    return "\n".join(lines)


# ─────────────────────────────────────────
# PERPLEXITY
# ─────────────────────────────────────────

def get_ai_news_summaries(history_context=""):
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

    history_section = f"\n\n{history_context}\n" if history_context else ""

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": f"""Tu es un expert en intelligence artificielle qui suit les véritables avancées technologiques du domaine.

Recherche sur le web les 5 actualités IA les plus impactantes publiées aujourd'hui ou dans les derniers jours.{history_section}
Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte Markdown, sans ``` et sans préambule.

Format JSON strict :
{{
  "date": "JJ/MM/AAAA",
  "news": [
    {{
      "title": "Titre de l'actualité",
      "summary": "Résumé détaillé en 4 phrases avec contexte, détails techniques et implications concrètes.",
      "why": "Pourquoi c'est important en 1-2 phrases.",
      "category": "Modèle|Entreprise|Recherche|Application|Régulation"
    }}
  ],
  "updates": [
    {{
      "title": "Titre de la mise à jour",
      "original": "Sujet original couvert récemment",
      "summary": "Ce qui a changé depuis, en 3-4 phrases.",
      "why": "Pourquoi ce changement est important.",
      "category": "Modèle|Entreprise|Recherche|Application|Régulation"
    }}
  ]
}}

RÈGLES STRICTES :
1. "news" contient TOUJOURS exactement 5 actualités. Jamais moins, jamais vide.
   - Chaque info doit être un fait ou angle totalement nouveau, absent de l'historique ci-dessus.
   - "news" et "updates" ne doivent jamais couvrir le même sujet.
   - Si les 5 news ne sont pas trouvées avec les priorités hautes, complète avec les meilleures actualités IA disponibles ce jour-là.

2. PRIORITÉS — dans cet ordre de préférence (mais toujours trouver 5 news) :
   a. Sortie ou annonce d'un nouveau modèle IA (GPT, Claude, Gemini, Llama, Mistral, etc.) : version, benchmarks, capacités
   b. Percée de recherche : nouveau papier scientifique majeur, résultat SOTA, architecture innovante
   c. Lancement de produit IA concret avec impact réel : nouvel outil, agent, fonctionnalité déployée
   d. Mouvement stratégique majeur : acquisition, levée de fonds significative, partenariat technique
   e. Régulation ou décision légale, ou autre actualité IA significative du jour

3. PRÉFÉRENCES (pas d'exclusions absolues) :
   - Préférer les faits techniques concrets aux simples déclarations
   - Préférer les événements avec impact direct sur la technologie ou les utilisateurs
   - Si une conférence a lieu, ne la mentionner QUE si une annonce concrète y a été faite

4. "updates" contient entre 0 et 2 évolutions de sujets déjà présents dans l'historique.
   - Ne mettre une update que si : sortie officielle d'un modèle annoncé, nouveaux benchmarks significatifs, revirement stratégique, incident ou faille majeure.
   - Si aucun critère n'est rempli, laisser "updates" vide : [].
   - Ne jamais inventer une mise à jour.
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
        raw = raw.strip()
        raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
        raw = re.sub(r'\n?```\s*$', '', raw).strip()

        data = json.loads(raw)
        print("✅ Résumés générés avec succès")
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API Perplexity : {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur parsing JSON : {e}")
        return None


# ─────────────────────────────────────────
# GITHUB
# ─────────────────────────────────────────

def ensure_gh_pages_branch(repo, headers):
    r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/main", headers=headers)
    if r.status_code != 200:
        r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/master", headers=headers)
    if r.status_code != 200:
        print("❌ Impossible de trouver la branche principale")
        return False
    sha = r.json()["object"]["sha"]
    payload = {"ref": "refs/heads/gh-pages", "sha": sha}
    r = requests.post(f"https://api.github.com/repos/{repo}/git/refs", json=payload, headers=headers)
    if r.status_code in (201, 422):
        print("✅ Branche gh-pages prête")
        return True
    print(f"❌ Erreur création gh-pages : {r.text}")
    return False


def push_file_to_gh_pages(repo, headers, filename, content_str, commit_message):
    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    sha = None
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        sha = r.json().get("sha")
    payload = {"message": commit_message, "content": encoded, "branch": "gh-pages"}
    if sha:
        payload["sha"] = sha
    r = requests.put(api_url, json=payload, headers=headers)
    r.raise_for_status()


def push_to_github(data, history):
    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    if not token or not repo:
        print("❌ GITHUB_TOKEN ou GITHUB_REPO manquant")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    ensure_gh_pages_branch(repo, headers)
    date_str = data.get('date', datetime.now().strftime('%d/%m/%Y'))

    try:
        # today.json
        push_file_to_gh_pages(repo, headers, "today.json",
            json.dumps(data, ensure_ascii=False, indent=2), f"digest: {date_str}")
        print("✅ today.json publié")

        # history.json
        push_file_to_gh_pages(repo, headers, "history.json",
            json.dumps(history, ensure_ascii=False, indent=2), f"history: {date_str}")
        print("✅ history.json mis à jour")

        # index.html
        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            html_content = html_content.replace("__PX_KEY_B64__", __import__("base64").b64encode(os.environ.get("PERPLEXITY_API_KEY","").encode()).decode())
            push_file_to_gh_pages(repo, headers, "index.html", html_content, "chore: update index.html")
            print("✅ index.html publié")

        return True

    except Exception as e:
        print(f"❌ Erreur push GitHub : {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails : {e.response.text}")
        return False


# ─────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────

def send_email(date_str, page_url):
    sender   = os.environ.get('SENDER_EMAIL')
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
        msg['From']    = sender
        msg['To']      = receiver
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("✅ Email envoyé avec succès !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print("\n" + "="*50)
    print("🤖 AI DAILY DIGEST — Démarrage")
    print("="*50 + "\n")

    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    gh_headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    } if token and repo else None

    # 1. Récupère l'historique des 7 derniers jours
    history = []
    if gh_headers:
        history = fetch_history(repo, gh_headers)
        print(f"📚 Historique chargé : {len(history)} jour(s)")

    history_context = build_history_context(history)

    # 2. Génère les news (jusqu'à 3 tentatives si résultat vide)
    data = None
    for attempt in range(3):
        data = get_ai_news_summaries(history_context)
        if data and len(data.get("news", [])) >= 5:
            break
        news_count = len(data.get("news", [])) if data else 0
        print(f"⚠️  Tentative {attempt+1}/3 — news obtenues : {news_count}/5, nouvelle tentative…")
    if not data or len(data.get("news", [])) == 0:
        print("❌ Impossible de générer les résumés après 3 tentatives")
        return

    # 3. Met à jour l'historique avec les news et mises à jour du jour
    history = update_history(history, data.get("news", []), data.get("updates", []))

    # 4. Pousse sur GitHub Pages
    pushed = push_to_github(data, history)
    if not pushed:
        print("⚠️  Données générées mais non publiées sur GitHub Pages")

    print("\n✅ Processus terminé !")


if __name__ == "__main__":
    main()
