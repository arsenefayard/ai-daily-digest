# AI Daily Digest

Script automatique qui envoie chaque jour un digest des 5 actualités IA les plus importantes.

## Technologies

- Python 3.10
- OpenAI API (GPT-4o-mini)
- GitHub Actions pour l'automatisation

## Configuration

Voir les instructions dans le code pour configurer les variables d'environnement.

## Lancer le workflow GitHub Actions à la main (local)

1. Copie `.env.example` vers `.env` (le fichier `.env` n’est **jamais** commité).
2. Mets ton PAT GitHub dans `.env` : `GITHUB_TOKEN=ghp_...` (permission **workflow**).
3. Depuis la racine du dépôt : `.\run-workflow.ps1`

Voir aussi `CONTEXTE-PROJET-ANTIGRAVITY.md`.

