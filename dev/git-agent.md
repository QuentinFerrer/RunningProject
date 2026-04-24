# Agent Git (développeur)

## Rôle
Assister dans les opérations git courantes.
Conventions et protocole complet dans `rules/git-workflow.md`.
La protection de `main` est assurée par GitHub (branch ruleset).

## Avant toute modification de code ou d'agent

Avant de toucher à un fichier `.py`, `.md` (hors `data/`), `.json` :

```bash
git branch -a
git status
```

Demander à l'utilisateur :
> "Sur quelle branche veux-tu travailler ?
> → Continuer sur une branche existante
> → Créer une nouvelle branche"

Nouvelle branche → toujours depuis `main` :
```bash
git checkout main
git pull origin main
git checkout -b feature/YYYY-MM-DD-sujet
```

## Commit

```bash
git status
git diff --stat
git add scripts/ agents/ rules/ dev/ hooks/ CLAUDE.md README.md requirements.txt .gitignore .env.example .gitattributes .claude/settings.json data/.gitkeep data/*.example.md
git commit -m "type: description courte"
```

## Push + Pull Request

```bash
git push origin nom-de-la-branche
gh pr create --title "titre" --body "description"
```

## Commandes utiles

```bash
git log --oneline -10    # Historique
git branch -a            # Toutes les branches
git diff --stat          # Résumé des changements
gh pr list               # PRs ouvertes
```
