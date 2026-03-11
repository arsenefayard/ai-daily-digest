"""
Script de digest quotidien science avec Perplexity API
"""
import os, json, re, requests, base64
from datetime import datetime

def fetch_history(repo, headers):
    api_url = f"https://api.github.com/repos/{repo}/contents/science_history.json"
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
    return []

def update_history(history, new_news, updates=None):
    titles = [item["title"] for item in new_news]
    if updates: titles += [item["title"] for item in updates]
    history.append({"date": datetime.now().strftime("%d/%m/%Y"), "titles": titles})
    return history[-7:]

def build_history_context(history):
    if not history: return ""
    lines = ["Actualités déjà couvertes ces derniers jours (à éviter sauf changement majeur) :"]
    for day in history:
        lines.append(f"\n{day['date']} :")
        for title in day["titles"]: lines.append(f"  - {title}")
    return "\n".join(lines)

def ensure_gh_pages(repo, headers):
    r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/main", headers=headers)
    if r.status_code != 200:
        r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/master", headers=headers)
    if r.status_code != 200: return False
    sha = r.json()["object"]["sha"]
    requests.post(f"https://api.github.com/repos/{repo}/git/refs",
        json={"ref": "refs/heads/gh-pages", "sha": sha}, headers=headers)
    return True

def push_file(repo, headers, filename, content_str, message):
    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    sha = None
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200: sha = r.json().get("sha")
    payload = {"message": message, "content": encoded, "branch": "gh-pages"}
    if sha: payload["sha"] = sha
    requests.put(api_url, json=payload, headers=headers).raise_for_status()

def push_to_github(data, history):
    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    if not token or not repo: return False
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    ensure_gh_pages(repo, headers)
    date_str = data.get('date', datetime.now().strftime('%d/%m/%Y'))
    try:
        push_file(repo, headers, "science_today.json", json.dumps(data, ensure_ascii=False, indent=2), f"science-digest: {date_str}")
        push_file(repo, headers, "science_history.json", json.dumps(history, ensure_ascii=False, indent=2), f"science-history: {date_str}")
        if os.path.exists("science.html"):
            push_file(repo, headers, "science.html", open("science.html", encoding="utf-8").read(), "chore: update science.html")
        return True
    except Exception as e:
        print(f"❌ Erreur push : {e}"); return False

def get_news(history_context=""):
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY non trouvée"); return None
    print("🔍 Recherche des actualités science...")
    history_section = f"\n\n{history_context}\n" if history_context else ""
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": f"""Tu es un assistant expert en actualités scientifiques et recherche fondamentale.

Recherche sur le web les 5 avancées scientifiques les plus importantes publiées aujourd'hui ou dans les derniers jours.{history_section}
Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte Markdown, sans ``` et sans préambule.

Format JSON strict :
{{
  "date": "JJ/MM/AAAA",
  "news": [
    {{
      "title": "Titre de l'actualité",
      "summary": "Résumé détaillé en 4 phrases avec contexte et implications concrètes.",
      "why": "Pourquoi c'est important en 1-2 phrases.",
      "category": "Physique|Chimie|Biologie|Maths|Espace|Médecine|Autre"
    }}
  ],
  "updates": [
    {{
      "title": "Titre de la mise à jour",
      "original": "Sujet original couvert récemment",
      "summary": "Ce qui a changé depuis, en 3-4 phrases.",
      "why": "Pourquoi ce changement est important.",
      "category": "Physique|Chimie|Biologie|Maths|Espace|Médecine|Autre"
    }}
  ]
}}

RÈGLES STRICTES :
1. "news" contient TOUJOURS exactement 5 actualités. Jamais moins, jamais vide.
   - Chaque info doit être un fait ou angle totalement nouveau, absent de l'historique ci-dessus.
   - "news" et "updates" ne doivent jamais couvrir le même sujet.

2. "updates" contient entre 0 et 2 évolutions de sujets déjà présents dans l'historique.
   - Ne mettre une update que si : confirmation d'une découverte, publication dans Nature ou Science, prix Nobel, réfutation d'une théorie, nouvelle mission spatiale.
   - Si aucun critère n'est rempli, laisser "updates" vide : [].
   - Ne jamais inventer une mise à jour.
Concentre-toi sur : physique (quantique, particules, cosmologie), chimie, biologie, mathématiques, exploration spatiale, médecine et génétique, climate science.
Réponds UNIQUEMENT avec le JSON, rien d'autre."""},
            {"role": "user", "content": f"Quelles sont les 5 avancées scientifiques les plus importantes des dernières 48 heures ? Date : {datetime.now().strftime('%d/%m/%Y')}"}
        ],
        "temperature": 0.2, "max_tokens": 2000
    }
    try:
        r = requests.post("https://api.perplexity.ai/chat/completions", json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        r.raise_for_status()
        raw = r.json()['choices'][0]['message']['content'].strip()
        raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
        raw = re.sub(r'\n?```\s*$', '', raw).strip()
        data = json.loads(raw)
        print("✅ Résumés générés"); return data
    except Exception as e:
        print(f"❌ Erreur : {e}"); return None


def main():
    print("\n" + "="*50 + f"\n🔬 SCIENCE DAILY DIGEST — Démarrage\n" + "="*50 + "\n")
    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    gh_headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"} if token and repo else None
    history = fetch_history(repo, gh_headers) if gh_headers else []
    print(f"📚 Historique : {len(history)} jour(s)")
    data = get_news(build_history_context(history))
    if not data: print("❌ Échec"); return
    history = update_history(history, data.get("news", []), data.get("updates", []))
    push_to_github(data, history)
    print(f"\n✅ Processus science terminé !")

if __name__ == "__main__":
    main()
