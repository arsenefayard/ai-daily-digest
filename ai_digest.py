"""
Script de digest quotidien IA avec Perplexity API
Génère un fichier JSON sur GitHub Pages et envoie un lien par email.
"""

import os
import json
import requests
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
                "content": f"""Tu es un assistant spécialisé dans les actualités IA.

Recherche sur le web les 5 actualités IA les plus importantes publiées aujourd'hui ou dans les derniers jours.{history_section}
RÈGLES SUR LES RÉPÉTITIONS :
- N'inclus pas une actualité déjà couverte si c'est la même information sans évolution.
- Inclus-la si l'un de ces critères est rempli :
  * Sortie officielle d'un modèle/produit annoncé précédemment
  * Chiffres ou performances significativement différents de ce qui était connu
  * Revirement stratégique d'une entreprise (rachat, partenariat, abandon)
  * Réaction en chaîne : d'autres acteurs majeurs réagissent à l'info initiale
  * Impact réglementaire ou légal nouveau sur le sujet
  * Incident, faille ou controverse qui change la perception du sujet
- Dans ce cas, place l'info dans le tableau "updates" du JSON, pas dans "news".

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

Génère exactement 5 objets dans "news" (nouvelles infos uniquement, jamais de sujets déjà couverts).
Pour "updates" : entre 0 et 2 objets maximum. Laisse le tableau vide ([]) s'il n'y a pas de mise à jour significative. N'invente pas de mises à jour — inclus uniquement des évolutions réelles et importantes sur des sujets déjà couverts cette semaine.
Critères pour une mise à jour : sortie officielle, nouveaux chiffres significatifs, revirement stratégique, réaction en chaîne majeure, impact légal nouveau, incident ou controverse.
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

    # 2. Génère les news en évitant les répétitions
    data = get_ai_news_summaries(history_context)
    if not data:
        print("❌ Impossible de générer les résumés")
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
