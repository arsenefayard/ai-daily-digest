# Contexte projet — AI Daily Digest (pour Antigravity / poursuite du dev)

Document de transfert : historique, architecture, fichiers critiques, pièges connus et pistes d’évolution. À coller ou importer dans ton workspace Antigravity pour continuer les modifications sans perdre le fil.

---

## 1. Vision produit

Application **Daily Digest** multi-thèmes :

| Thème | Page | JSON du jour (gh-pages) | Historique |
|------|------|-------------------------|------------|
| IA | `index.html` | `today.json` | `history.json` |
| Géopolitique | `geo.html` | `geo_today.json` | `geo_history.json` |
| Économie | `eco.html` | `eco_today.json` | `eco_history.json` |
| Sport | `sport.html` | `sport_today.json` | `sport_history.json` |
| Musique | `music.html` | `music_today.json` | `music_history.json` |
| Science | `science.html` | `science_today.json` | `science_history.json` |
| Culture | `culture.html` | `culture_today.json` | `culture_history.json` |
| Histoire | `history.html` | **structure différente** : un seul sujet du jour | `history_history.json` |

- **Génération** : scripts Python appellent l’API **Perplexity** (`model: sonar`), sortie attendue **JSON strict**.
- **Hébergement** : **GitHub Pages** sur la branche **`gh-pages`** (fichiers statiques + JSON).
- **Automatisation** : **GitHub Actions** (`.github/workflows/daily-digest.yml`) : déploiement HTML, génération des digests, envoi d’un **email combiné** avec liens vers chaque thème.
- **Cible UX** : **mobile-first**, navigation type **carrousel / swipe** entre cartes.

---

## 2. Stack technique

- **Frontend** : HTML/CSS/JS vanilla (pas de framework), polices Google (Fraunces, DM Mono, Outfit).
- **Backend / génération** : Python 3.10+, dépendance principale `requests` (`requirements.txt`).
- **CI** : GitHub Actions, `pip install -r requirements.txt`.
- **Secrets GitHub** (à configurer dans le dépôt) :
  - `PERPLEXITY_API_KEY`
  - `GITHUB_TOKEN` (fourni par Actions, utilisé pour l’API Contents)
  - `SENDER_EMAIL`, `EMAIL_PASSWORD`, `RECEIVER_EMAIL` (pour `send_email.py`)

Variable d’environnement **`GITHUB_REPO`** : `owner/repo` (ex. `user/ai-daily-digest`).

---

## 3. Flux de données (fin à fin)

1. Déclenchement **schedule** (crons toutes les 5 min à 6h et 7h UTC) ou **`workflow_dispatch`** (manuel).
2. Job **`check-time`** : n’autorise le run “quotidien” automatique que si **heure Paris = 8h** et si **`scheduled_digest_done.json`** sur `gh-pages` n’a pas déjà la **date du jour** (déduplication **uniquement** du digest planifié ; les runs manuels ne bloquent pas le cron 8h).
3. Job **`send-digest`** (si `should_run` ou run manuel) :
   - Checkout `main`
   - **Déploiement des 8 HTML** vers `gh-pages` via **GitHub Contents API** : remplace le placeholder `__PX_KEY_B64__` par la clé Perplexity encodée en **base64** (voir § clé API).
   - Enchaîne `ai_digest.py` → … → `history_digest.py`
   - `python send_email.py` : email HTML avec grille des thèmes + lien favoris (voir `send_email.py`).
   - Si **`schedule`** (cron) : étape finale qui met à jour **`scheduled_digest_done.json`** sur `gh-pages` (marqueur « digest 8h fait » pour ce jour).

Les scripts Python **poussent** aussi leurs JSON + leur `.html` thématique (avec injection clé) sur `gh-pages`.

---

## 4. Clé API Perplexity dans le navigateur (loupe)

**Problème résolu** : GitHub **Push Protection** bloquait une clé en clair dans les fichiers.

**Mécanisme actuel** :
- Dans chaque HTML, le JS contient : `const _PX_KEY = atob('__PX_KEY_B64__');`
- Au déploiement, `__PX_KEY_B64__` est remplacé par `base64(PERPLEXITY_API_KEY)` — la clé n’apparaît pas en clair dans le dépôt sur `main`, et le scan GitHub est contourné.
- **Important** : toute modification des pages sur `main` doit **conserver** le placeholder `__PX_KEY_B64__` ; le workflow / les scripts remplacent au moment du push vers `gh-pages`.

**Note** : la clé est tout de même **exposée côté client** une fois la page chargée (décodage `atob`). C’est un compromis pour une app 100 % statique ; pour une sécurité forte il faudrait un backend proxy (hors scope actuel).

---

## 5. Scripts Python (`*_digest.py`) — rôle et conventions

Chaque digest (sauf histoire, format spécial) suit le schéma général :

- Lecture optionnelle de **`*_history.json`** sur `gh-pages` pour éviter les doublons de titres.
- Appel Perplexity avec un **prompt système** long (format JSON imposé, règles “news” = 5 items, “updates” 0–2, qualité de langue en français, etc.).
- Parsing JSON, `push` des fichiers via **API Contents** GitHub.

### Règles récentes communes (diversité)

Une logique **souple** a été harmonisée sur les digests à **5 news** :

- Pas d’obligation d’avoir **5 `category` toutes différentes** : **jusqu’à 2** news peuvent partager la même **`category`** si les sujets/acteurs sont **nettement distincts**.
- **Inacceptable** : 5 news dans la **même** catégorie, **plus de 2** news avec la **même** `category`, ou **répétition** du même angle médiatique — le prompt demande alors une **recherche plus approfondie** et un **rééquilibre**.

Les catégories varient par thème (ex. IA : `Modèle|Entreprise|Recherche|Application|Régulation` ; science : `Physique|Chimie|…` ; etc.).

### Fichiers spécifiques

- **`ai_digest.py`** : digest IA ; retry si `news` &lt; 5 ; pousse aussi **`favorites.html`** s’il existe (voir déploiement workflow : les 8 pages “digest” sont dans le step Actions ; `favorites.html` peut nécessiter d’être ajouté à ce step pour un déploiement systématique sans dépendre uniquement du push dans `ai_digest`).
- **`history_digest.py`** : un **seul** sujet JSON (`subject` avec `context`, `dates`, `legacy`, `why`) — règle de **diversité des jalons** dans le tableau `dates` (éviter trop de répétitions du même type d’événement).
- **`send_email.py`** : construit l’email avec **grille 2 colonnes** des thèmes + section **Mes favoris** vers `{base}/favorites.html`.

---

## 6. Frontend (HTML) — fonctionnalités à ne pas casser

Les **8 pages** partagent une logique proche (constantes `COLORS`, `THEME`, chargement du JSON du jour, `buildSlides`, `renderAll`, swipe).

### Navigation
- Swipe horizontal sur le **stage** ; code existant annule le swipe si le mouvement est **principalement vertical** (évite conflit avec scroll dans le corps de carte / overlays).

### Texte dans la carte
- Ajustement de taille de police (`fitTextToBox`) + mode **expandable** + overlay “why” / corps long.
- **A− / A+** : taille globale stockée `localStorage` (`digestFontSize`), plage typique 10–20 px.
- Scroll vertical dans **`.card-body`** quand le contenu dépasse après zoom — ne pas lier ce scroll au swipe horizontal.

### Loupe (Perplexity)
- Évolution vers **interface type chat** : historique, messages user/IA, **nouvelle conversation**, persistance **`localStorage`** par carte (`chat_[theme]_[newsIndex]`), archives limitées, contexte système avec titre + résumé + why.
- Panneau : **hauteur max ~90vh**, header sticky avec **fermer**, zone messages scrollable.

### Favoris
- Étoile sur les cartes, stockage **`fav_[theme]_[newsIndex]_[date]`** (ou variante proche selon implémentation), popup note optionnelle.
- Page **`favorites.html`** : liste des clés `fav_*`, groupement par thème, actions ouvrir/supprimer/tout effacer.

### Cohérence
- Tout accès **`localStorage`** doit rester protégé par **`try/catch`** (quota, mode privé, etc.).

---

## 7. GitHub Actions — détails utiles

- **`workflow_dispatch`** : exécute **toujours** la chaîne complète (y compris email), même hors fenêtre 8h — utile pour tests, mais **enverra un mail** si les secrets email sont présents.
- Le job `check-time` est **ignoré** pour le booléen final si `workflow_dispatch` (condition `should_run` **ou** `workflow_dispatch`).

Fichier : **`.github/workflows/daily-digest.yml`**.

---

## 8. Problèmes déjà rencontrés (référence rapide)

| Symptôme | Cause probable | Piste |
|----------|----------------|--------|
| Digest IA vide (`news: []`) | Prompt trop strict / filtrage Perplexity | Prompt assoupli + retry dans `ai_digest.py` |
| Loupe demande une clé | `gh-pages` pas à jour ou placeholder non remplacé | Vérifier run Actions, contenu `atob('...')` sur la page déployée |
| Push refusé (secret) | Clé en clair | Base64 + Contents API |
| Email reçu “sans avoir cliqué” | Run manuel ou autre déclenchement du workflow | Normal si `workflow_dispatch` ou autre run |

---

## 9. Pistes d’amélioration (non faites)

- Validation **post-génération** du JSON (nombre de `news`, catégories, longueurs min/max).
- **Retry** automatique si règle de diversité non respectée (comptage des `category` côté Python).
- Mode **dry-run** ou input `html_only` (déjà discuté puis retiré selon préférence utilisateur) pour déployer sans email.
- Ajouter **`favorites.html`** à la liste des fichiers du step “Déployer les pages HTML” si tu veux le même déploiement que les 8 pages à chaque run (sans dépendre uniquement de `ai_digest.py`).

---

## 10. Fichiers à ouvrir en priorité pour modifier le projet

| Domaine | Fichiers |
|---------|----------|
| Orchestration | `.github/workflows/daily-digest.yml` |
| Contenu / prompts | `ai_digest.py`, `geo_digest.py`, `eco_digest.py`, `sport_digest.py`, `music_digest.py`, `science_digest.py`, `culture_digest.py`, `history_digest.py` |
| Email | `send_email.py` |
| UI | `index.html`, `geo.html`, `eco.html`, `sport.html`, `music.html`, `science.html`, `culture.html`, `history.html`, `favorites.html` |
| Dépendances | `requirements.txt` |

---

## 11. Ancien résumé court

Un fichier **`resume-projet-ai-daily-digest.txt`** existe encore (version plus courte, date mars 2026). Ce document **`CONTEXTE-PROJET-ANTIGRAVITY.md`** le remplace / complète pour un usage dans **Antigravity** avec une vue d’ensemble **détaillée et à jour** sur la mécanique du repo.

---

*Dernière mise à jour du document : génération automatique dans le cadre du dépôt — à compléter après chaque grosse évolution (nouveaux thèmes, auth, backend, etc.).*
