# Règles — Workflow Git

## Protection de main

La branche `main` est protégée par GitHub (branch ruleset).
**Aucun push direct n'est possible** — tout passe par une Pull Request.
Cette règle est appliquée au niveau réseau par GitHub, indépendamment des règles locales.

## Convention de nommage des branches

| Type | Format | Exemple |
|------|--------|---------|
| Nouvelle fonctionnalité | `feature/YYYY-MM-DD-sujet` | `feature/2026-04-25-nutrition-agent` |
| Correction de bug | `fix/YYYY-MM-DD-sujet` | `fix/2026-04-25-strava-token` |
| Mise à jour de règles | `rules/YYYY-MM-DD-sujet` | `rules/2026-04-25-recovery-thresholds` |
| Mise à jour d'agent | `agent/YYYY-MM-DD-sujet` | `agent/2026-04-25-setup-flow` |

## Protocole avant toute modification de code ou d'agent

**Déclencheur** : toute demande de modification sur `.py`, `.md` (hors `data/`), `.json`.

### 1. Afficher les branches existantes
```bash
git branch -a
git status
```

### 2. Demander à l'utilisateur
> "Sur quelle branche veux-tu travailler ?
> Branches existantes : [liste]
> → Continuer sur une branche existante
> → Créer une nouvelle branche"

### 3a. Branche existante
```bash
git checkout nom-de-la-branche
```

### 3b. Nouvelle branche — toujours depuis main
```bash
git checkout main
git pull origin main
git checkout -b feature/YYYY-MM-DD-sujet
```

### 4. Confirmer avant de modifier
```bash
git branch --show-current
```

## Cycle de travail

```
1. Modifications sur la branche feature
2. git add <fichiers spécifiques>   ← jamais git add -A
3. git commit -m "type: description"
4. git push origin nom-de-la-branche
5. gh pr create (sur demande)       ← GitHub bloque le merge sans PR
```

## Fichiers autorisés dans un commit

| Autorisé ✅ | Interdit ❌ |
|------------|------------|
| `scripts/*.py` | `.env` |
| `agents/*.md` | `data/running.db` |
| `rules/*.md` | `data/profile.md` |
| `hooks/*.py` | `data/calendar.md` |
| `CLAUDE.md` | `data/feedbacks.md` |
| `README.md` | `.venv/` |
| `.env.example` | `personal/` |
| `data/*.example.md` | |
| `data/.gitkeep` | |
