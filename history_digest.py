"""
Script de digest quotidien Histoire avec Perplexity API
Génère un point historique (personnalité ou événement) avec dates clés et contexte.
"""
import os, json, re, requests, base64
from datetime import datetime

def fetch_history(repo, headers):
    api_url = f"https://api.github.com/repos/{repo}/contents/history_history.json"
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
    return []

def update_history(history, subject_name):
    history.append({
        "date": datetime.now().strftime("%d/%m/%Y"),
        "subject": subject_name
    })
    return history[-30:]  # Garde 30 jours pour éviter les répétitions

def build_history_context(history):
    if not history:
        return ""
    lines = ["Sujets déjà couverts récemment (à ne pas répéter) :"]
    for day in history:
        lines.append(f"  - {day['subject']} ({day['date']})")
    return "\n".join(lines)

def ensure_gh_pages(repo, headers):
    r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/main", headers=headers)
    if r.status_code != 200:
        r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/master", headers=headers)
    if r.status_code != 200:
        return False
    sha = r.json()["object"]["sha"]
    requests.post(f"https://api.github.com/repos/{repo}/git/refs",
        json={"ref": "refs/heads/gh-pages", "sha": sha}, headers=headers)
    return True

def push_file(repo, headers, filename, content_str, message):
    api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    sha = None
    r = requests.get(api_url, headers=headers, params={"ref": "gh-pages"})
    if r.status_code == 200:
        sha = r.json().get("sha")
    payload = {"message": message, "content": encoded, "branch": "gh-pages"}
    if sha:
        payload["sha"] = sha
    requests.put(api_url, json=payload, headers=headers).raise_for_status()

def push_to_github(data, history):
    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    if not token or not repo:
        return False
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    ensure_gh_pages(repo, headers)
    date_str = data.get('date', datetime.now().strftime('%d/%m/%Y'))
    try:
        push_file(repo, headers, "history_today.json",
            json.dumps(data, ensure_ascii=False, indent=2), f"history-digest: {date_str}")
        print("✅ history_today.json publié")

        push_file(repo, headers, "history_history.json",
            json.dumps(history, ensure_ascii=False, indent=2), f"history-history: {date_str}")
        print("✅ history_history.json mis à jour")

        if os.path.exists("history.html"):
            _h = open("history.html", encoding="utf-8").read().replace("__PERPLEXITY_KEY__", os.environ.get("PERPLEXITY_API_KEY", ""))
            push_file(repo, headers, "history.html", _h, "chore: update history.html")
            print("✅ history.html publié")

        return True
    except Exception as e:
        print(f"❌ Erreur push : {e}"); return False

def get_history_point(history_context=""):
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY non trouvée"); return None

    print("🔍 Génération du point historique...")
    history_section = f"\n\n{history_context}\n" if history_context else ""

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": f"""Tu es un historien passionné et pédagogue. Tu dois choisir et présenter un point historique marquant : une personnalité, un événement, une civilisation, une découverte ou un mouvement historique.{history_section}
Choisis un sujet varié, instructif et peu connu du grand public. Alterne les catégories : philosophes, scientifiques, conquistadors, révolutions, empires, batailles décisives, inventeurs, artistes majeurs, civilisations disparues, traités historiques, etc. Varie les époques (Antiquité, Moyen-Âge, Renaissance, Époque moderne, XXe siècle) et les régions du monde.

Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte Markdown, sans ``` et sans préambule.

Format JSON strict :
{{
  "date": "JJ/MM/AAAA",
  "subject": {{
    "name": "Nom complet ou intitulé de l'événement",
    "type": "Personnalité|Événement|Civilisation|Découverte|Mouvement|Bataille|Révolution",
    "period": "Période ou dates (ex: 1452 – 1519 · Renaissance italienne)",
    "context": "Contexte détaillé en 5-6 phrases : origines, parcours ou déroulement, contributions ou conséquences majeures, faits marquants peu connus.",
    "dates": [
      {{"year": "AAAA ou siècle", "label": "Événement clé concis"}},
      {{"year": "AAAA", "label": "Événement clé concis"}},
      {{"year": "AAAA", "label": "Événement clé concis"}},
      {{"year": "AAAA", "label": "Événement clé concis"}},
      {{"year": "AAAA", "label": "Événement clé concis"}}
    ],
    "legacy": "Héritage en 3-4 phrases : impact durable, influence sur le monde actuel, postérité culturelle ou scientifique.",
    "why": "Pertinence ou leçon actuelle en 1-2 phrases percutantes."
  }}
}}

RÈGLES :
- "dates" contient entre 4 et 6 entrées, dans l'ordre chronologique, couvrant les moments clés
- "context" ne répète pas les informations de "dates" : c'est une narration, pas une liste
- "why" doit surprendre ou apporter un éclairage inattendu
- Évite les sujets trop génériques (Napoléon, Christophe Colomb, Einstein) sauf si l'angle est très original
- Réponds UNIQUEMENT avec le JSON, rien d'autre."""
            },
            {
                "role": "user",
                "content": f"Présente-moi un point historique fascinant pour aujourd'hui. Date : {datetime.now().strftime('%d/%m/%Y')}"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        r = requests.post("https://api.perplexity.ai/chat/completions", json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        r.raise_for_status()
        raw = r.json()['choices'][0]['message']['content'].strip()
        raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
        raw = re.sub(r'\n?```\s*$', '', raw).strip()
        data = json.loads(raw)
        print(f"✅ Point historique généré : {data['subject']['name']}")
        return data
    except Exception as e:
        print(f"❌ Erreur : {e}"); return None


def main():
    print("\n" + "=" * 50 + f"\n📜 HISTORY DAILY DIGEST — Démarrage\n" + "=" * 50 + "\n")
    token = os.environ.get('GITHUB_TOKEN')
    repo  = os.environ.get('GITHUB_REPO')
    gh_headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"} if token and repo else None

    history = fetch_history(repo, gh_headers) if gh_headers else []
    print(f"📚 Historique : {len(history)} sujet(s) déjà couverts")

    data = get_history_point(build_history_context(history))
    if not data:
        print("❌ Échec"); return

    subject_name = data.get("subject", {}).get("name", "")
    history = update_history(history, subject_name)
    push_to_github(data, history)
    print(f"\n✅ Processus history terminé !")


if __name__ == "__main__":
    main()
