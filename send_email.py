"""Script d'envoi de l'email combine - tous les digests."""
import html
import os
import re
import smtplib
import unicodedata
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

_MONTHS_FR = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)

_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "et", "en", "un", "une", "a", "au",
    "aux", "pour", "sur", "dans", "avec", "par", "qui", "que", "est", "son",
    "sa", "ses", "vers", "plus", "apres", "avant", "face", "entre", "meta",
    "lance", "annonce", "publie", "nouveau", "nouvelle", "premier", "jour",
    "cette", "suite", "selon", "contre", "mars", "avril", "mai",
}

_SIGNALS = {
    "ia": [
        ("Innovation", ["modele", "llm", "gpt", "sonar", "agent", "inference"]),
        ("Regulation", ["regulation", "loi", "compliance", "directive", "autorite"]),
        ("Strategie", ["ecosysteme", "positionnement", "partenariat", "acteur"]),
        ("Produit", ["copilot", "assistant", "application", "lancement", "version"]),
        ("Industrie", ["concurrence", "editeur", "entreprise", "marche"]),
    ],
    "geo": [
        ("Securite", ["guerre", "frappe", "offensive", "front", "missile"]),
        ("Diplomatie", ["sommet", "accord", "negociation", "alliance", "onu"]),
        ("Sanctions", ["sanction", "embargo", "restriction", "douane"]),
        ("Gouvernance", ["election", "vote", "coalition", "parlement", "president"]),
        ("Energie", ["gaz", "petrole", "nucleaire", "pipeline", "opec"]),
    ],
    "eco": [
        ("Marches", ["marche", "bourse", "indice", "actions", "obligation"]),
        ("Monetaire", ["taux", "banque centrale", "fed", "bce", "inflation"]),
        ("Entreprise", ["resultats", "fusion", "acquisition", "restructuration"]),
        ("Macro", ["croissance", "conjoncture", "activite", "pib", "emploi"]),
        ("Crypto", ["bitcoin", "crypto", "blockchain", "etf"]),
    ],
    "sport": [
        ("Competitions", ["ligue", "championnat", "tournoi", "grand prix"]),
        ("Transferts", ["transfert", "mercato", "signature", "contrat"]),
        ("Performances", ["record", "victoire", "finale", "classement"]),
        ("Enjeux", ["blessure", "forfait", "retour", "suspension"]),
        ("Calendrier", ["saison", "journee", "phase", "playoff"]),
    ],
    "music": [
        ("Sorties", ["album", "single", "ep", "sortie", "track"]),
        ("Tournees", ["tournee", "concert", "festival", "scene"]),
        ("Industrie", ["label", "streaming", "droits", "catalogue"]),
        ("Artistes", ["groupe", "chanteur", "guitariste", "metal", "rock"]),
        ("Audience", ["classement", "top", "billboard", "ecoutes"]),
    ],
    "science": [
        ("Recherche", ["etude", "publication", "laboratoire", "revue"]),
        ("Sante", ["medecine", "clinique", "gene", "therapie", "virus"]),
        ("Espace", ["nasa", "spacex", "orbite", "mission", "satellite"]),
        ("Physique", ["quantique", "particule", "energie", "matiere"]),
        ("Climat", ["climat", "ocean", "temperature", "co2"]),
    ],
    "culture": [
        ("Idees", ["philo", "essai", "debat", "societe", "ethique"]),
        ("Cinema", ["film", "festival", "realisateur", "sortie"]),
        ("Medias", ["plateforme", "audience", "serie", "documentaire"]),
        ("Tendances", ["tendance", "culture", "viral", "reseau"]),
        ("Patrimoine", ["histoire", "musee", "archive", "heritage"]),
    ],
    "history": [
        ("Contexte", ["empire", "royaume", "republique", "civilisation"]),
        ("Chronologie", ["siecle", "annee", "periode", "regne"]),
        ("Pouvoirs", ["bataille", "campagne", "alliance", "frontiere"]),
        ("Personnalites", ["roi", "general", "philosophe", "explorateur"]),
        ("Heritage", ["memoire", "impact", "tradition", "transmission"]),
    ],
}


def _norm(text):
    t = unicodedata.normalize("NFKD", str(text or ""))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.lower()


def _extract_titles(payload):
    titles = []
    if not isinstance(payload, dict):
        return titles
    news = payload.get("news")
    if isinstance(news, list):
        titles.extend([n.get("title", "") for n in news if isinstance(n, dict)])
    updates = payload.get("updates")
    if isinstance(updates, list):
        titles.extend([u.get("title", "") for u in updates if isinstance(u, dict)])
    subject = payload.get("subject")
    if isinstance(subject, dict):
        titles.append(subject.get("name", ""))
    return [t for t in titles if t]


def _fallback_parts(fallback):
    vals = [x.strip() for x in re.split(r"[,&]", fallback) if x.strip()]
    return vals[:3]


def _format_triptych(parts):
    vals = [p for p in parts if p]
    if len(vals) >= 3:
        return f"{vals[0]}, {vals[1]} & {vals[2]}"
    if len(vals) == 2:
        return f"{vals[0]}, {vals[1]} & Perspectives"
    if len(vals) == 1:
        return f"{vals[0]}, Analyse & Perspectives"
    return "Analyse, Tendances & Perspectives"


def _keywords_from_titles(titles, section_key, fallback):
    blob = _norm(" | ".join(titles))
    if not blob.strip():
        return _format_triptych(_fallback_parts(fallback))

    scored = []
    for label, hints in _SIGNALS.get(section_key, []):
        score = 0
        for hint in hints:
            if hint in blob:
                score += 1
        if score:
            scored.append((score, label))
    scored.sort(reverse=True)

    labels = []
    for _, label in scored:
        if label not in labels:
            labels.append(label)
        if len(labels) == 3:
            break
    if len(labels) >= 2:
        if len(labels) < 3:
            for extra in _fallback_parts(fallback):
                if extra not in labels:
                    labels.append(extra)
                if len(labels) == 3:
                    break
        return _format_triptych(labels)

    tokens = re.findall(r"[A-Za-z0-9'-]+", blob)
    freq = {}
    for tok in tokens:
        tok = tok.strip("'-")
        if len(tok) < 5 or tok in _STOPWORDS:
            continue
        freq[tok] = freq.get(tok, 0) + 1
    top = [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]
    if top:
        return _format_triptych([w.capitalize() for w in top])
    return _format_triptych(_fallback_parts(fallback))


def _fetch_caption(base, path, section_key, fallback):
    try:
        r = requests.get(f"{base}/{path}", timeout=8)
        if not r.ok:
            return html.escape(_format_triptych(_fallback_parts(fallback)))
        titles = _extract_titles(r.json())
        caption = _keywords_from_titles(titles, section_key, fallback)
        return html.escape(caption)
    except Exception:
        return html.escape(_format_triptych(_fallback_parts(fallback)))


def _card(label, color, caption, href, padding):
    return (
        f'<a href="{href}" style="display:block;padding:{padding};text-decoration:none;color:inherit;">'
        f'<div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:{color};'
        f'font-family:Arial,sans-serif;margin-bottom:10px;">{label}</div>'
        f'<div style="font-size:14px;font-weight:700;color:#f0ede6;line-height:1.3;'
        f'font-family:Georgia,serif;">{caption}</div>'
        f'<div style="margin-top:14px;">'
        f'<span style="font-size:9px;letter-spacing:1.6px;text-transform:uppercase;'
        f'color:{color};font-family:Arial,sans-serif;">Lire &rarr;</span></div></a>'
    )


def send_combined_email():
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("RECEIVER_EMAIL")
    repo = os.environ.get("GITHUB_REPO", "")
    if not all([sender, password, receiver]):
        print("Variables email manquantes")
        return False

    username = repo.split("/")[0] if "/" in repo else ""
    reponame = repo.split("/")[1] if "/" in repo else ""
    base = f"https://{username}.github.io/{reponame}"
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    date_header = f"{now.day} {_MONTHS_FR[now.month - 1]} {now.year}"
    year = now.year

    cap_ia = _fetch_caption(base, "today.json", "ia", "Innovation, Regulation & Strategie")
    cap_geo = _fetch_caption(base, "geo_today.json", "geo", "Securite, Diplomatie & Gouvernance")
    cap_eco = _fetch_caption(base, "eco_today.json", "eco", "Marches, Macro & Monetaire")
    cap_sport = _fetch_caption(base, "sport_today.json", "sport", "Competitions, Enjeux & Performances")
    cap_music = _fetch_caption(base, "music_today.json", "music", "Sorties, Industrie & Audience")
    cap_science = _fetch_caption(base, "science_today.json", "science", "Recherche, Sante & Espace")
    cap_culture = _fetch_caption(base, "culture_today.json", "culture", "Idees, Cinema & Tendances")
    cap_history = _fetch_caption(base, "history_today.json", "history", "Contexte, Chronologie & Heritage")

    html_body = f"""
<html>
<head>
  <meta charset="UTF-8">
  <meta name="color-scheme" content="dark only">
  <meta name="supported-color-schemes" content="dark">
  <meta name="x-apple-disable-message-reformatting">
  <style>
    :root {{ color-scheme: dark; }}
    body, table, td, div, p, span, a {{
      color-scheme: dark !important;
      forced-color-adjust: none !important;
    }}
  </style>
</head>
<body bgcolor="#1a1a1a" style="margin:0;padding:0;background-color:#1a1a1a !important;color:#f0ede6 !important;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#1a1a1a" style="background-color:#1a1a1a !important;">
<tr><td align="center" style="padding:30px 16px;">
<table width="560" cellpadding="0" cellspacing="0" border="0" bgcolor="#222222" style="background-color:#222222 !important;max-width:560px;">
  <tr>
    <td bgcolor="#1a1a1a" style="background-color:#1a1a1a !important;padding:26px 30px 20px;border-bottom:1px solid #2a2a2a;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td>
          <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#555;font-family:Arial,sans-serif;margin-bottom:8px;">{date_header} &middot; Edition matinale</div>
          <div style="font-size:32px;font-weight:700;color:#f0ede6;line-height:1;font-family:Georgia,serif;">DAILY<br>BRIEFING</div>
          <div style="margin-top:14px;height:2px;width:40px;background:#c8a96e;"></div>
        </td>
        <td align="right" valign="top"><div style="font-size:9px;letter-spacing:2px;color:#444;font-family:Arial,sans-serif;">VOL. 01</div></td>
      </tr></table>
    </td>
  </tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="50%" bgcolor="#2d3d2e" style="background:#2d3d2e;padding:0;vertical-align:top;">{_card("Intelligence Artificielle", "#5aaa72", cap_ia, f"{base}/", "22px 20px")}</td>
    <td width="2" style="background:#111;"></td>
    <td width="50%" bgcolor="#1e2a38" style="background:#1e2a38;padding:0;vertical-align:top;">{_card("Geopolitique", "#4a88c0", cap_geo, f"{base}/geo.html", "22px 20px")}</td>
  </tr></table></td></tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="50%" bgcolor="#382a1a" style="background:#382a1a;padding:0;vertical-align:top;">{_card("Economie &amp; Finance", "#c8862a", cap_eco, f"{base}/eco.html", "22px 20px")}</td>
    <td width="2" style="background:#111;"></td>
    <td width="50%" bgcolor="#38201e" style="background:#38201e;padding:0;vertical-align:top;">{_card("Sport", "#c84a4a", cap_sport, f"{base}/sport.html", "22px 20px")}</td>
  </tr></table></td></tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td style="padding:0;"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="33%" bgcolor="#261e38" style="background:#261e38;padding:0;vertical-align:top;">{_card("Musique", "#7a5cc8", cap_music, f"{base}/music.html", "18px 16px")}</td>
    <td width="1" style="background:#111;"></td>
    <td width="33%" bgcolor="#1a2e28" style="background:#1a2e28;padding:0;vertical-align:top;">{_card("Sciences", "#2a9e7a", cap_science, f"{base}/science.html", "18px 16px")}</td>
    <td width="1" style="background:#111;"></td>
    <td width="33%" bgcolor="#2e1a28" style="background:#2e1a28;padding:0;vertical-align:top;">{_card("Culture", "#c84a8a", cap_culture, f"{base}/culture.html", "18px 16px")}</td>
  </tr></table></td></tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td bgcolor="#2a2010" style="background:#2a2010;padding:0;">
    <a href="{base}/history.html" style="display:block;padding:18px 22px;text-decoration:none;color:inherit;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td>
          <div style="font-size:8px;letter-spacing:2.5px;text-transform:uppercase;color:#a07840;font-family:Arial,sans-serif;margin-bottom:6px;">Histoire</div>
          <div style="font-size:14px;font-weight:700;color:#f0ede6;font-family:Georgia,serif;">{cap_history}</div>
        </td>
        <td align="right" valign="bottom" style="padding-left:14px;">
          <span style="font-size:9px;letter-spacing:1.6px;text-transform:uppercase;color:#a07840;font-family:Arial,sans-serif;">Lire &rarr;</span>
        </td>
      </tr></table>
    </a>
  </td></tr>
  <tr><td style="height:2px;background:#111;"></td></tr>

  <tr><td bgcolor="#1e1c10" style="background:#1e1c10;padding:14px 22px;border-top:1px solid #2a2418;">
    <a href="{base}/favorites.html" style="display:block;text-decoration:none;color:inherit;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td><span style="font-size:13px;color:#c8a96e;">&#9733;</span><span style="font-size:9px;letter-spacing:2.5px;text-transform:uppercase;color:#c8a96e;font-family:Arial,sans-serif;font-weight:700;margin-left:10px;">Mes Favoris</span></td>
        <td align="right" style="padding-left:22px;white-space:nowrap;"><span style="font-size:9px;letter-spacing:1.6px;text-transform:uppercase;color:#554f3a;font-family:Arial,sans-serif;">Retrouver &rarr;</span></td>
      </tr></table>
    </a>
  </td></tr>

  <tr><td bgcolor="#111111" style="background:#111111;padding:12px 24px;border-top:1px solid #1e1e1e;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">Diffusion restreinte &middot; Usage professionnel</td>
      <td align="right" style="font-size:9px;color:#333;letter-spacing:1.5px;text-transform:uppercase;font-family:Arial,sans-serif;">{year}</td>
    </tr></table>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""

    recipients = [r.strip() for r in receiver.split(",") if r.strip()]
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Daily Briefing - {date_str}"
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        print(f"Email combine envoye a {len(recipients)} destinataire(s).")
        return True
    except Exception as e:
        print(f"Erreur : {e}")
        return False


if __name__ == "__main__":
    import sys

    sys.exit(0 if send_combined_email() else 1)
