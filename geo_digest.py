"""
Script de digest quotidien Géopolitique avec Perplexity API
Génère un fichier JSON sur GitHub Pages et envoie un lien par email.
"""

import os
import json
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
    api_url = f"https://api.github.com/repos/{repo}/contents/geo_history.json"
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return json.loads(content)
    return []


def update_history(history, new_news, updates=None):
    titles = [item["title"] for item in new_news]
    if updates:
        titles += [item["title"] for item in updates]
    today = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "titles": titles
    }
    history.append(today)
    return history[-7:]


def build_history_context(history):
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

def get_geo_news_summaries(history_context=""):
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ Erreur : PERPLEXITY_API_KEY non trouvée")
        return None

    print("🔍 Recherche des actualités géopolitiques avec Perplexity...")

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
                "content": f"""Tu es un assistant spécialisé dans la géopolitique mondiale.

Recherche sur le web les 5 actualités géopolitiques les plus importantes publiées aujourd'hui ou dans les derniers jours.{history_section}
RÈGLES SUR LES RÉPÉTITIONS :
- N'inclus pas une actualité déjà couverte si c'est la même information sans évolution.
- Inclus-la si l'un de ces critères est rempli :
  * Escalade ou désescalade militaire significative
  * Changement de position diplomatique d'un acteur majeur
  * Accord, traité ou rupture diplomatique
  * Sanctions économiques ou levée de sanctions
  * Élection ou changement de pouvoir influençant les rapports de force
  * Incident majeur (attaque, catastrophe, crise humanitaire) qui change la donne
- Dans ce cas, place l'info dans le tableau "updates" du JSON, pas dans "news".

Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte Markdown, sans ``` et sans préambule.

Format JSON strict :
{{
  "date": "JJ/MM/AAAA",
  "news": [
    {{
      "title": "Titre de l'actualité",
      "summary": "Résumé détaillé en 4 phrases avec contexte, enjeux et implications géopolitiques concrètes.",
      "why": "Pourquoi c'est important en 1-2 phrases.",
      "category": "Conflit|Diplomatie|Économie|Élection|Énergie|Sécurité"
    }}
  ],
  "updates": [
    {{
      "title": "Titre de la mise à jour",
      "original": "Sujet original couvert récemment",
      "summary": "Ce qui a changé depuis, en 3-4 phrases.",
      "why": "Pourquoi ce changement est important.",
      "category": "Conflit|Diplomatie|Économie|Élection|Énergie|Sécurité"
    }}
  ]
}}

Génère exactement 5 objets dans "news" (nouvelles infos uniquement, jamais de sujets déjà couverts).
Pour "updates" : entre 0 et 2 objets maximum. Laisse le tableau vide ([]) s'il n'y a pas de mise à jour significative.
Concentre-toi sur : conflits armés, diplomatie internationale, économie mondiale, élections majeures, énergie et ressources, sécurité internationale.
Réponds UNIQUEMENT avec le JSON, rien d'autre."""
            },
            {
                "role": "user",
                "content": f"Quelles sont les 5 actualités géopolitiques les plus importantes des dernières 48 heures ? Date : {datetime.now().strftime('%d/%m/%Y')}"
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
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
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
        push_file_to_gh_pages(repo, headers, "geo_today.json",
            json.dumps(data, ensure_ascii=False, indent=2), f"geo-digest: {date_str}")
        print("✅ geo_today.json publié")

        push_file_to_gh_pages(repo, headers, "geo_history.json",
            json.dumps(history, ensure_ascii=False, indent=2), f"geo-history: {date_str}")
        print("✅ geo_history.json mis à jour")

        if os.path.exists("geo.html"):
            with open("geo.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            push_file_to_gh_pages(repo, headers, "geo.html", html_content, "chore: update geo.html")
            print("✅ geo.html publié")

        return True
    except Exception as e:
        print(f"❌ Erreur push GitHub : {e}")
        return False


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print("\n" + "="*50)
    print("🌍 GEO DAILY DIGEST — Démarrage")
    print("="*50 + "\n")

    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    gh_headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    } if token and repo else None

    history = []
    if gh_headers:
        history = fetch_history(repo, gh_headers)
        print(f"📚 Historique chargé : {len(history)} jour(s)")

    history_context = build_history_context(history)
    data = get_geo_news_summaries(history_context)
    if not data:
        print("❌ Impossible de générer les résumés")
        return

    history = update_history(history, data.get("news", []), data.get("updates", []))
    push_to_github(data, history)

    print("\n✅ Processus géopolitique terminé !")


if __name__ == "__main__":
    main()
